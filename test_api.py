import data.fmr_data as fmr
fmr.API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI2IiwianRpIjoiNTA1NDU0NGU4MWM4YTdkNDgzZDhkOWUwYzdlN2U3ZTQxMDZiNjNmMDVjZjdhNTkyYTZkNjgwMjFkY2E3NTA2NWMzNDU2N2NjNDlmNDJkOGQiLCJpYXQiOjE3NzM4NzY3MzguNjgxMTg3LCJuYmYiOjE3NzM4NzY3MzguNjgxMTkxLCJleHAiOjIwODk0OTU5MzguNjY4Njk2LCJzdWIiOiIxMTk4MTEiLCJzY29wZXMiOltdfQ.dWAZV0bXm7_3S0pSTDven4FmhcXZqNKTbf3J9pCX2MJym8Atp9GzVexMhU3H0ECn68IdPtnKzCmDw_IMTa1mPA"

print("Loading master dataset...")
df = fmr.get_master_df()
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print("\nSample with income data:")
print(df[df["median_income"] > 0][["display_name", "state_code", "br2_fmr", "median_income", "rent_burden_pct", "burden_category"]].head(10))