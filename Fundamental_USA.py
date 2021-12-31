import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pandas_datareader import data as pdr
import yfinance as yf
import requests


# SETTING PAGE CONFIG TO WIDE MODE
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# Read CSV
@st.cache(persist=True)
def getFile(f):
    df = pd.read_csv(f, sep=';', decimal='.', thousands=',')
    return df

@st.cache(persist=True)
def getDataProcessamento(url):
    response = requests.get(url)
    ultima_atualizacao = response.text
    return ultima_atualizacao

f = 'https://raw.githubusercontent.com/renatosts/Fundamental_USA/main/DadosFinanceirosEUA.csv'
#f = 'DadosFinanceirosEUA.csv'
financ = getFile(f)

f = 'https://raw.githubusercontent.com/renatosts/Fundamental_USA/main/submissions.csv'
#f = 'submissions.csv'
submissions = getFile(f)

url = 'https://raw.githubusercontent.com/renatosts/Fundamental_USA/main/processamento.txt'
ultima_atualizacao = getDataProcessamento(url)

st.sidebar.write(f"Last update: {ultima_atualizacao}")

check_sp500 = st.sidebar.checkbox("Only S&P 500", value=True)
if check_sp500:
    financ = financ[financ.sp500]

check_nasdaq100 = st.sidebar.checkbox("Only Nasdaq 100")
if check_nasdaq100:
    financ = financ[financ.nasdaq100]

check_reit = st.sidebar.checkbox("Only REIT")
if check_reit:
    financ = financ[financ.sicDescription == 'Real Estate Investment Trusts']


ticker_selecionado = ''
ticker = ''
empresa = ''

row1_1, row1_2 = st.columns([4, 7])

with row1_1:
    # Prepara lista de empresas
    ticker_opcoes =  financ.tickers + ' ; ' + financ.name + ' ; ' + financ.sicDescription
    ticker_opcoes = ticker_opcoes.drop_duplicates().sort_values()

    if len(ticker_opcoes) > 0:
        ticker_selecionado = st.selectbox('Select the company:', ticker_opcoes)
        ticker = ticker_selecionado.split(sep=';')[0].strip()
        empresa = ticker_selecionado.split(sep=';')[1].strip()

# FILTERING DATA (limitando aos 11 últimos anos - tail)
df = financ[financ.tickers == ticker].tail(11).copy()
#print(df)

if df.rec_liq.iloc[-1] > 100_000_000:
    conversao_div = 1_000_000
    conversao = 'US$ in millions'
elif df.rec_liq.iloc[-1] > 100_000:
    conversao_div = 1_000
    conversao = 'US$ in thousands'
else:
    conversao_div = 1
    conversao = 'US$'

df.rec_liq = (df.rec_liq / conversao_div).astype('int64')
df.lucro_liq = (df.lucro_liq / conversao_div).astype('int64')
df.EBITDA = (df.EBITDA / conversao_div).astype('int64')
df.caixa = (df.caixa / conversao_div).astype('int64')
df.pl = (df.pl / conversao_div).astype('int64')
df.div_total = (df.div_total / conversao_div).astype('int64')

df.fechamento= pd.to_datetime(df.fechamento).dt.strftime('%d/%m/%Y')

df.loc[df.form.str.startswith('10-K'), 'form'] = 'A'
df.loc[df.form.str.startswith('10-Q'), 'form'] = 'Q'

df = df.fillna(0)

qtd_acoes = df.shares.iloc[0]

df['ano'] = df.end.str[0:4].astype(int)

if len(df) > 1:
    if df.ano.iloc[-1] == df.ano.iloc[-2]:
        df.ano.iloc[-1] = df.ano.iloc[-1] + 1

df_aux = df[['ano', 'form', 'rec_liq', 'lucro_liq', 'margem_liq', 'EBITDA', 'div_liq', 'caixa', 'pl', 'div_total', 'fechamento', 'accn']]

df_aux.reset_index(inplace=True, drop=True) 
df_aux = df_aux.set_index('ano')

df_aux.columns = ['A/Q', 'Net Sale', 'Net Profit', 'Net Rate', 'EBITDA', 'Net Liability', 'Cash', 'Equity', 'Total Liability', 'Form Date', 'Form']

df_aux = df_aux.style.format(thousands=".",
                             decimal = ",",
                             formatter={'Net Rate': '{:.2f}',
                                        'Net Liability': '{:.2f}'})

# EXIBE DATAFRAME
with row1_1:
    st.write(df.name.iloc[0])
    st.write(f'Tickers: {df.tickers.iloc[0]}')
    st.write(f'Exchanges: {df.exchanges.iloc[0]}')
    st.write(f'{df.sicDescription.iloc[0]}')
    st.write(f'S&P 500: {df.sp500.iloc[-1]}; Nasdaq 100: {df.nasdaq100.iloc[-1]}')

with row1_2:
    st.dataframe(df_aux)
    st.write(f'{conversao}; A/Q: Annual/Quarterly Form; https://www.sec.gov/edgar/browse/?CIK={df.cik.iloc[0]}')



fig = make_subplots(rows=2, cols=2, 
                    shared_xaxes=True,
                    vertical_spacing=0.1,
                    specs=([[{'secondary_y': True}, {'secondary_y': True}],
                            [{'secondary_y': True}, {'secondary_y': True}]]))

fig.add_trace(
    go.Bar(x=df.ano, y=df.rec_liq, name='Net Sale', marker=dict(color="blue")),
    row=1, col=1)
fig.add_trace(
    go.Bar(x=df.ano, y=df.EBITDA, name='EBITDA', marker=dict(color="green")),
    row=1, col=1)

 
fig.add_trace(
    go.Bar(x=df.ano, y=df.lucro_liq, marker=dict(color="yellow"), name='Net Profit'), 
    secondary_y=False,
    row=1, col=2)
fig.add_trace(
    go.Scatter(x=df.ano, y=df.margem_liq, marker=dict(color="crimson"), name='Net Rate'), 
    secondary_y=True,
    row=1, col=2)

fig.add_trace(
    go.Bar(x=df.ano, y=df.div_liq, marker=dict(color="red"), showlegend=True, name='Net Liability'),
    row=2, col=1)

fig.add_trace(
    go.Bar(x=df.ano, y=df.pl, name='Equity', marker=dict(color="purple")),
    row=2, col=2)
fig.add_trace(
    go.Bar(x=df.ano, y=df.caixa, name='Cash', marker=dict(color="cyan")),
    row=2, col=2)


fig.update_layout(barmode='overlay', separators = '.,',)

fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=1,
    xanchor="right",
    x=1))

st.plotly_chart(fig, use_container_width=True)

# Cotações
ticker_b3 = []
if len(df) > 0:
    ticker_b3 = df.tickers[df.tickers == ticker].iloc[0].split(sep=',')

row1_1, row1_2 = st.columns([1, 1])


for tck in ticker_b3:

    df_nyse = pdr.DataReader(f'{tck}', data_source='yahoo', start=f'2010-01-01')
    
    #print(df_nyse)

    # Cálculo do P/L diário

    df_nyse['Ano'] = df_nyse.index.year
    df_nyse['Data'] = df_nyse.index
    df_nyse = df_nyse.merge(df, how='left', left_on='Ano', right_on='ano')
    df_nyse['P/L'] = df_nyse.Close / (df_nyse.lucro_liq * conversao_div / qtd_acoes)

    # Limita intervalo do P/L entre -150 e 150
    df_nyse.loc[df_nyse['P/L'] > 150, 'P/L'] = 150
    df_nyse.loc[df_nyse['P/L'] < -150, 'P/L'] = -150

    df_pl_hist = df_nyse.tail(500)
    

    var = (df_nyse["Adj Close"].iloc[-1] / df_nyse["Adj Close"].iloc[-2] - 1) * 100

    with row1_1:

        fig = go.Figure(data=[
            go.Scatter(x=df_nyse["Data"], y=df_nyse["Adj Close"], marker=dict(color="darkgoldenrod"))])
        fig.update_layout(title=f'<b>{tck}     (US$ {df_nyse["Adj Close"].iloc[-1]:,.2f})   <i> {var:,.2f} % </i></b>')

        st.plotly_chart(fig)

    
    with row1_2:
        
        fig = go.Figure(data=[
            go.Scatter(x=df_pl_hist["Data"], y=df_pl_hist["P/L"], marker=dict(color="green"))])
        fig.update_layout(title=f'<b>Historic P/E ({df_pl_hist["P/L"].iloc[-1]:,.2f})    (Shares: {qtd_acoes:,.0f})</b>')

        st.plotly_chart(fig)
    

# Prepara lista de empresas
df_submissions = submissions[['name', 'tickers', 'exchanges', 'sicDescription', 'fiscalYearEnd', 'cik', 'sp500', 'nasdaq100']].copy()

col1, col2, col3, col4 = st.columns(4)

with col1:
    sub_check_sp500 = st.checkbox("S&P 500", value=True)
    if sub_check_sp500:
        df_submissions = df_submissions[df_submissions.sp500]

with col2:
    sub_check_nasdaq100 = st.checkbox("Nasdaq 100")
    if sub_check_nasdaq100:
        df_submissions = df_submissions[df_submissions.nasdaq100]


sub_description =  ['(ALL)'] + submissions.sicDescription.drop_duplicates().sort_values().to_list()
sub_description_selecionado = st.selectbox('Sector:', sub_description )
if sub_description_selecionado != '(ALL)':
    df_submissions = df_submissions[df_submissions.sicDescription == sub_description_selecionado]

st.dataframe(df_submissions)
