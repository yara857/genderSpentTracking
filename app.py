import streamlit as st
import pandas as pd
from collections import defaultdict
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.user import User
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from datetime import datetime, timedelta
import plotly.express as px

# ===================== Credentials =====================
team_credentials = {
    "qaoud": {"username": "qaoud_user", "password": "qaoud_pass"},
    "taher": {"username": "taher_user", "password": "taher_pass"},
    "admin": {"username": "admin", "password": "admin_pass"}  # Admin user
}

teams = {
    "qaoud": {"act_1110493866779936", "act_2552907308215563", "act_1024932058694649",
              "act_484794044494250", "act_491661666975935", "act_3783876785259320", "act_808836814588501",
              "act_1465342538192806", "act_349419674831825", "act_605590368701495", "act_1106920700810737",
              "act_495393796683804", "act_3917900671783321", "act_1032918741385206", "act_1873860226413296",
              "act_820067853430864", "act_1832609284326278", "act_1831681447773953", "act_525111343230393",
              "act_1111033107846239", "act_446143675092721", "act_3735033723398649", "act_1160917978500634",
              "act_481045498013949", "act_1438264286880701", "act_913634477428214", "act_1257976282245126",
              "act_880045560717824", "act_1500284387257195", "act_2223009838063616", "act_1683951949050858",
              "act_1591281524753725", "act_1054012229279958", "act_503501265565688", "act_472782225604827",
              "act_686659513241205", "act_480818408256462", "act_271107602165124", "act_803931941918015",
              "act_802531705496302", "act_1965207844273941", "act_6138155329624196", "act_833746338442042",
              "act_2764339257041054", "act_668534158600329", "act_416735438053499", "act_1150733472876801",
              "act_1611735449470819", "act_1622576991673636", "act_530650696518461", "act_659166860256794",
              "act_806904932282718", "act_1473911003823398", "act_799199789486116", "act_1551490619628527",
              "act_858483333273309", "act_3614857042002825", "act_4164085090539188", "act_790182993795341",
              "act_749499958118518", "act_1468273327760869", "act_1299177688654545", "act_790856167227835","act_802531705496302","act_806904932282718"},
    "taher": {
        "act_1122033631798415", "act_1573944913033077", "act_1449776175430067",
        "act_461392002996920", "act_378525045233709", "act_941916861325221",
        "act_1925625627955953", "act_850056290595951", "act_3876212252698351",
        "act_7949479881827692", "act_577926371246983", "act_1807970279737291",
        "act_1069345594937651", "act_2227598254277390", "act_537517202274301",
        "act_1193325865062689", "act_1652622545469088", "act_1033571434639050",
        "act_860397696266577", "act_569341712749669", "act_1747046902753277",
        "act_1097303645310610", "act_517798987807178", "act_1624624092271535",
        "act_501956059557382", "act_399947229848173", "act_2041103139723714",
        "act_1391794181816851", "act_613618428335002", "act_1177029914077193",
        "act_1365280811345488",  "act_9204702042967493" , "act_663917829898406", 
        "act_1279091416916908" ,"act_3436750296477609" ,"act_25054115470891040" , 
        "act_740406192112484", "act_1580260726708657" ,"act_879968637353721" , 
        "act_1190001252905279" ,"act_1847086306101737" ,"act_1158202939150021",
        "act_1098324938321349","act_768517845342716","act_522493803883485","act_1067465375364660",
        "act_1261470998247775","act_830221765934179","act_1001278395040670", "act_809557281930666",
        "act_1220817715856094", "act_1748258275946991","act_768517845342716","act_1740318363203985","act_1374295137658799", "act_577254217595912"
        
    }
}

# ===================== Facebook API Setup =====================
access_token = "EAAIObOmY9V4BPrkIlmtbU5YrIxrUYK27NZBPxQBoZCMa2ojeiPq4iRrjww5jARZAzbQOZAn5ycZAl5bQoVt6SLvBV4Sae7JEXhTlY1LsDIoND625O4ZCEdrLZCXE2WtPUwMAtJK4V5XoP3MPiwhNZCezKXwrMNqoYT0mdk8ssoVxnLrj3uEfnGEOvYJZBAxR8"
FacebookAdsApi.init(access_token=access_token)
me = User(fbid='me')
accounts = me.get_ad_accounts(fields=['id', 'name'])

# ===================== Date Setup =====================
today = datetime.today()
first_of_month = today.replace(day=1)
since_date = first_of_month.strftime('%Y-%m-%d')
until_date = today.strftime('%Y-%m-%d')

# ===================== Streamlit Login =====================
st.title("Facebook Ads Gender Spend Dashboard")
st.sidebar.header("Login")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

# Authenticate
logged_in_team = None
is_admin = False
for team, creds in team_credentials.items():
    if username == creds['username'] and password == creds['password']:
        if team == "admin":
            is_admin = True
        else:
            logged_in_team = team
        break

if not logged_in_team and not is_admin:
    st.warning("Please enter valid username and password.")
    st.stop()

if is_admin:
    st.success("Logged in as Admin")
else:
    st.success(f"Logged in as {logged_in_team}")

# ===================== Fetch Insights =====================
team_gender_totals = defaultdict(lambda: defaultdict(lambda: {'Female': 0, 'Male': 0}))

for account in accounts:
    account_id = account['id']
    account_name = account['name']

    # Identify team
    account_team = next((team for team, ids in teams.items() if account_id in ids), None)
    if not account_team:
        continue  # Skip accounts not in any team

    # Only fetch for admin or the logged-in team
    if not is_admin and account_team != logged_in_team:
        continue

    try:
        insights = AdAccount(account_id).get_insights(
            params={
                'time_range': {'since': since_date, 'until': until_date},
                'fields': [AdsInsights.Field.spend],
                'breakdowns': ['gender']
            }
        )

        for insight in insights:
            gender = insight.get('gender', 'Unknown').capitalize()
            if gender not in ['Male', 'Female']:
                continue  # Skip Unknown

            spend = float(insight.get('spend', 0.0))
            if spend > 0:
                team_gender_totals[account_team][account_name][gender] += spend

    except Exception as e:
        st.error(f"Error fetching data for account {account_name}: {e}")

# ===================== Prepare Data =====================
rows = []
for team_name, accounts_data in team_gender_totals.items():
    for account_name, genders in accounts_data.items():
        total = genders['Female'] + genders['Male']
        if total == 0:
            continue
        pct_female = round(genders['Female'] / total * 100, 2)
        pct_male = round(genders['Male'] / total * 100, 2)
        rows.append({
            'Team': team_name,
            'Account Name': account_name,
            'Female Spend': genders['Female'],
            'Male Spend': genders['Male'],
            'Pct Female': pct_female,
            'Pct Male': pct_male
        })

df = pd.DataFrame(rows)

# ===================== Display Table =====================
if df.empty:
    st.info("No accounts with Male or Female spend found.")
else:
    if is_admin:
        st.subheader("All Teams Accounts")
        team_filter = st.selectbox("Select Team to Filter (Optional)", options=["All"] + list(teams.keys()))
        if team_filter != "All":
            display_df = df[df['Team'] == team_filter]
        else:
            display_df = df
    else:
        st.subheader(f"Accounts for {logged_in_team}")
        display_df = df

    st.dataframe(display_df)

    # ===================== Donut Chart =====================
    st.subheader("Overall Gender Spend")
    donut_data = display_df.melt(id_vars=['Account Name'], value_vars=['Female Spend', 'Male Spend'],
                                 var_name='Gender', value_name='Spend')
    donut_data['Gender'] = donut_data['Gender'].str.replace(' Spend', '')
    fig = px.pie(
        donut_data,
        names='Gender',
        values='Spend',
        hole=0.4,
        title="Overall Gender Spend"
    )
    st.plotly_chart(fig, use_container_width=True)
