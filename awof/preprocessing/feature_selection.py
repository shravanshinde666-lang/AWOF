def apply(df,context):
 removed={};target=context.target_column
 for col in list(context.feature_columns):
  if df[col].nunique(dropna=False)<=1: removed[col]="constant"
  elif col.lower().endswith("id") or col.lower()=="id": removed[col]="identifier_candidate"
 context.working_dataframe=df.drop(columns=list(removed),errors="ignore")
 context.feature_columns=[c for c in context.working_dataframe.columns if c!=target]
 return {"features_before":len(df.columns)-(1 if target else 0),"features_after":len(context.feature_columns),"removed_features":list(removed),"reason_per_feature":removed}
