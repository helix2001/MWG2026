from pandas import DataFrame, read_csv, set_option
set_option('display.max_rows', 10)

dados = read_csv('d:/MWG_data/ISAVIA_2024/Reykjavik_20240801.csv',delimiter=',')
dados.loc[dados['f073_timeof_rx_pos'].isna() | dados['flight_id'].isna()]

dados = dados.dropna().sort_values(by=['flight_id','f073_timeof_rx_pos','lat','lon'], ascending= True).drop_duplicates(subset=['flight_id','f073_timeof_rx_pos','lat','lon']).iloc[::5]
new = dados[['flight_id','ots','fix_timestamps','fix_lats','fix_lons','aircraft_type_text','rad_nav_equipment','ssr_equipment','otherinfo_text']].drop_duplicates(subset=['flight_id'])

new['profile_timestamps'] = new['fix_timestamps'].apply(lambda x: x.split(';') if x is not None else [])
new['profile_lats'] = new['fix_lats'].str.split(';')
new['profile_lons'] = new['fix_lons'].str.split(';')

new.drop(columns=['fix_timestamps','fix_lats','fix_lons'], axis=1, inplace=True)

dados = dados.drop(columns=['ots','fix_timestamps','fix_lats','fix_lons','aircraft_type_text','rad_nav_equipment','ssr_equipment','otherinfo_text'], axis = 1)

print(new)

print(dados)