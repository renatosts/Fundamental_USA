from datetime import datetime
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
st.set_page_config(
    layout='wide',
    initial_sidebar_state='collapsed',
    page_icon='app.jpg',
    page_title='USA')

# Read CSV
@st.cache(persist=True)
def getFile(f):
    df = pd.read_csv(f, sep=';', decimal=',')
    return df

@st.cache(persist=True)
def getLPA(f):
    df = pd.read_csv(f, sep=';', decimal=',')
    return df

@st.cache(persist=True)
def getDataProcessamento(url):
    response = requests.get(url)
    ultima_atualizacao = response.text
    return ultima_atualizacao

f = 'https://raw.githubusercontent.com/renatosts/Fundamental_USA/main/DadosFinanceirosEUA.csv'
#f = 'DadosFinanceirosEUA.csv'
financ = getFile(f)

f = 'https://raw.githubusercontent.com/renatosts/Fundamental_USA/main/lpa.csv'
#f = 'lpa.csv'
lpa = getLPA(f)

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
    ticker_opcoes =  financ.ticker + ' ; ' + financ.name + ' ; ' + financ.sic_title
    ticker_opcoes = ticker_opcoes.drop_duplicates().sort_values()

    if len(ticker_opcoes) > 0:
        ticker_selecionado = st.selectbox('Select the company:', ticker_opcoes)
        ticker = ticker_selecionado.split(sep=';')[0].strip()
        empresa = ticker_selecionado.split(sep=';')[1].strip()

# FILTERING DATA (limitando aos 11 últimos anos - tail)
df = financ[financ.ticker == ticker].tail(11).copy()

cik_selecionado = df.cik.iloc[0]
#print(df)

moeda = df.uom.iloc[-1]

if df.rec_liq.iloc[-1] > 100_000_000:
    conversao_div = 1_000_000
    conversao = f'{moeda} in millions'
elif df.rec_liq.iloc[-1] > 100_000:
    conversao_div = 1_000
    conversao = f'{moeda} in thousands'
else:
    conversao_div = 1
    conversao = moeda

df.rec_liq = (df.rec_liq / conversao_div).astype('int64')
df.lucro_liq = (df.lucro_liq / conversao_div).astype('int64')
df.EBITDA = (df.EBITDA / conversao_div).astype('int64')
df.caixa = (df.caixa / conversao_div).astype('int64')
df.pl = (df.pl / conversao_div).astype('int64')
df.div_total = (df.div_total / conversao_div).astype('int64')

df.period = pd.to_datetime(df.period).dt.strftime('%d/%m/%Y')

df = df.fillna(0)

df['ano'] = df.period.str[6:10].astype(int)

if len(df) > 1:
    if df.ano.iloc[-1] == df.ano.iloc[-2]:
        df.ano.iloc[-1] = df.ano.iloc[-1] + 1

df_aux = df[['ano', 'fp', 'rec_liq', 'lucro_liq', 'margem_liq', 'EBITDA', 'div_liq', 'caixa', 'pl', 'div_total', 'LPA', 'period', 'adsh']]

df_aux.reset_index(inplace=True, drop=True) 
df_aux = df_aux.set_index('ano')

df_aux.columns = ['Y/Q', 'Net Sale', 'Net Profit', 'Net Rate', 'EBITDA', 'Net Liability', 'Cash', 'Equity', 'Total Liability', 'EPS', 'Form Date', 'Form']

df_aux = df_aux.style.format(thousands=".",
                             decimal = ",",
                             formatter={'Net Rate': '{:.2f}',
                                        'Net Liability': '{:.2f}',
                                        'EPS': '{:.2f}'})

# EXIBE DATAFRAME
with row1_1:
    st.write(df.name.iloc[0])
    st.write(f'Ticker: {df.ticker.iloc[0]}')
    st.write(f'{df.cityba.iloc[0]} {df.countryba.iloc[0]}')
    #st.write(f'Exchanges: {df.exchanges.iloc[0]}')
    st.write(f'{df.sic_title.iloc[0]}')
    st.write(f'S&P 500: {df.sp500.iloc[-1]}; Nasdaq 100: {df.nasdaq100.iloc[-1]}')

with row1_2:
    st.dataframe(df_aux)
    st.write(f'{conversao}; https://www.sec.gov/edgar/browse/?CIK={df.cik.iloc[0]}')



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

df_lpa = lpa[lpa.cik == cik_selecionado].copy()
df_lpa.period = pd.to_datetime(df_lpa.period)

if len(df) > 0:
    ticker_b3 = df.ticker[df.ticker == ticker].iloc[0].split(sep=',')


row1_1, row1_2 = st.columns([1, 1])

dt_hoje = datetime.today().strftime('%Y-%m-%d')

for tck in ticker_b3:

    # Cálculo do P/L diário

    df_datas = pd.DataFrame(pd.date_range(start='2018-01-01', end=dt_hoje), columns=['Date'])

    df_nyse = pdr.DataReader(f'{tck}', data_source='yahoo', start=f'2020-01-01').reset_index()
    
    df_nyse = df_datas.merge(df_nyse, on='Date', how='left' )

    df_nyse = df_nyse.merge(df_lpa, how='left', left_on='Date', right_on='period')
    df_nyse = df_nyse.ffill()
    df_nyse['P/L'] = df_nyse['Adj Close'] / df_nyse['LPA']

    # Limita intervalo do P/L entre -150 e 150
    #df_nyse.loc[df_nyse['P/L'] > 150, 'P/L'] = 150
    #df_nyse.loc[df_nyse['P/L'] < -150, 'P/L'] = -150

    df_pl_hist = df_nyse.tail(1000)
    
    print(df_pl_hist)

    var = (df_nyse["Adj Close"].iloc[-1] / df_nyse["Adj Close"].iloc[-2] - 1) * 100

    with row1_1:

        fig = go.Figure(data=[
            go.Scatter(x=df_nyse["Date"], y=df_nyse["Adj Close"], marker=dict(color="darkgoldenrod"))])
        fig.update_layout(title=f'<b>{tck}     (US$ {df_nyse["Adj Close"].iloc[-1]:,.2f})   <i> {var:,.2f} % </i></b>')

        st.plotly_chart(fig)

    
    with row1_2:
        
        fig = go.Figure(data=[
            go.Scatter(x=df_nyse["Date"], y=df_nyse["P/L"], marker=dict(color="green"))])
        fig.update_layout(title=f'<b>Historic P/E ({df_nyse["P/L"].iloc[-1]:,.2f})</b>')

        st.plotly_chart(fig)
    

# Prepara lista de empresas
companies = financ.drop_duplicates(['name', 'ticker', 'sic_title', 'fye', 'cik', 'sp500', 'nasdaq100'])[
    ['name', 'ticker', 'sic_title', 'fye', 'cik', 'sp500', 'nasdaq100']]

companies = companies.sort_values('name')

col1, col2, col3, col4 = st.columns(4)

with col1:
    sub_check_sp500 = st.checkbox("S&P 500", value=True)
    if sub_check_sp500:
        companies = companies[companies.sp500]

with col2:
    sub_check_nasdaq100 = st.checkbox("Nasdaq 100")
    if sub_check_nasdaq100:
        companies = companies[companies.nasdaq100]


sub_description =  ['(ALL)'] + companies.sic_title.drop_duplicates().sort_values().to_list()
sub_description_selecionado = st.selectbox('Sector:', sub_description )
if sub_description_selecionado != '(ALL)':
    companies = companies[companies.sic_title == sub_description_selecionado]

st.dataframe(companies)
