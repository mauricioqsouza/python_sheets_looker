import requests
import json
import gspread
import pandas as pd
import numpy as np
from google.oauth2 import service_account
from datetime import date
import time
from datetime import datetime
from pandas import json_normalize
import io
import re

#Preparando o google Planilhas como Base:

scopes = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

json_file = "autentication_2020.json"

def login():
    credentials = service_account.Credentials.from_service_account_file(json_file)
    scoped_credentials = credentials.with_scopes(scopes)
    gc = gspread.authorize(scoped_credentials)
    return gc


gc = login()
print("LOGIN da API do Sheets, Realizado!")

#Abre a planilha
sheet = gc.open_by_key('1gJlSrs2Gu3ZvWyDnF746DNmEXExL0Te4nu85wFAESUc')

#Selecionando a WORKSHEET:
guia01 = sheet.worksheet("BD_DASHBOARD")

##Fim da preparação do Google Planilhas.

#DF Analytics:
analytics = pd.read_excel("Analytics - Case Study.xlsx",sheet_name= 'analytics')

print(analytics)

#VERIFICAÇÃO DE DUPLICADOS:
print(analytics.duplicated().sum())

analytics = analytics.drop_duplicates()

print(analytics)

#DF Transacional:
transacional = pd.read_excel("Case Study (1).xlsx",sheet_name= 'transacional')

print(transacional)

#VERIFICAÇÃO DE DUPLICADOS:
print(transacional.duplicated().sum())

transacional = transacional.drop_duplicates()

print(transacional)

#JOIN:

df3 = analytics.join(transacional.set_index('id_pedido'), on='transactionId', rsuffix= ' - 2')

print(df3.info())
print (df3)
df3['medium'] = df3['medium'].astype(str)


def criterio_canais(cc_df3):
    if((re.search(cc_df3['campaign'], r"-(FB|IG|IS|YT|TW).*-(ORG|PER)-")and(re.search(cc_df3['campaign'], r"infl\|mic|paid_social|paid social|\(not set\)|\b(PRO|RET|NL|PS|INF|MIC)\b")==None))or(re.search(cc_df3['source'], r"instagram.(perfil|stories|shopping)|youtube|facebook|linkedin|pinterest|twitter|whatsapp")and(re.search(cc_df3['campaign'], r"infl\|mic|paid_social|paid social|\(not set\)|\b(PRO|RET|NL|PS|INF|MIC)\b")==None))):
        return "Social CM"
    elif((re.search(cc_df3['campaign'], r"\b(-INF-|-MIC-)\b")and(re.search(cc_df3['campaign'], r"paid social|social cm|paid_social|social_cm")==None))or(re.search(cc_df3['source'], r"instagram_stories|instagram stories")and(re.search(cc_df3['campaign'], r"paid social|social cm|paid_social|social_cm")==None))):
        return "Influencers"
    elif ((re.search(cc_df3['campaign'], r"\b(PS|NL(_.*)?)\b")) or (
                  re.search(cc_df3['source'], r"newsletter|email|transaccionales|carrito abandonado|bienvenida|referidos|klaviyo|presta"))):
        return "Email"
    elif ((re.search(cc_df3['source'], r"google|bing") and ((
                  cc_df3['medium'] == "cpc")
            )) or (
                  re.search(cc_df3['campaign'], r"\b(GA|BG).*\b(RET|PRO)\b"))):
        return "Paid Search"
    elif ((re.search(cc_df3['campaign'], r"\b(FB|IG|IS|MC).*\b(RET|PRO)\b"))):
        return "Paid Social"
    elif ((re.search(cc_df3['source'], r"\b(youtube|facebook|instagram|linkedin|pinterest|twitter)\b")) or (re.search(cc_df3['medium'], "social"))):
        return "Organic Social"
    elif ((re.search(cc_df3['campaign'], r"\b(-GD-|-CR-)\b")) or (re.search(cc_df3['source'], r"^(criteo)$"))):
        return "Display"
    elif ((re.search(cc_df3['medium'], r"referral"))):
        return "Referral"
    elif ((re.search(cc_df3['medium'], r"organic"))):
        return "Organic Search"
    elif ((re.search(cc_df3['medium'], r"\(none\)"))):
        return "Direct"
    else:
        return ""

df3['Canal'] = df3.apply(criterio_canais, axis=1)

df3 = df3.fillna(np.nan).replace([np.nan], "")

#df3['importe'] = df3['importe'].astype(str)
#df3['id_cliente'] = df3['id_cliente'].astype(str)
df3['fecha_pedido'] = df3['fecha_pedido'].astype(str)


print(df3)
print(df3.info())

df3.to_excel('Case Study.xlsx', sheet_name='DF3_Join')

#Colar o df no G Sheets:
guia01.update([df3.columns.values.tolist()] + df3.values.tolist())

print("Dados copiados e exportados para o G Sheets!")