from sklearn.preprocessing import StandardScaler
def apply(df,context):
 cols=[c for c in context.feature_columns if str(df[c].dtype).startswith(("int","float")) and df[c].nunique()>2]
 if cols:
  scaler=StandardScaler();context.working_dataframe[cols]=scaler.fit_transform(df[cols]);context.artifacts["scaler"]=scaler
 return {"columns_scaled":cols,"scaler_type":"StandardScaler"}
