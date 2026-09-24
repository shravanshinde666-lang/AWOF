import pandas as pd
def apply(df,context):
 result=df.copy();meta={"columns_processed":[],"strategy_per_column":{},"values_imputed":0,"target_missing_count":int(result[context.target_column].isna().sum()) if context.target_column else 0}
 for c in context.feature_columns:
  n=int(result[c].isna().sum())
  if not n:continue
  if pd.api.types.is_numeric_dtype(result[c]):v=result[c].median();strategy="median"
  else:
   mode=result[c].mode();v=mode.iloc[0] if not mode.empty else "Unknown";strategy="mode_or_unknown"
  result[c]=result[c].fillna(v);meta["columns_processed"].append(c);meta["strategy_per_column"][c]=strategy;meta["values_imputed"]+=n
 context.working_dataframe=result;return meta
