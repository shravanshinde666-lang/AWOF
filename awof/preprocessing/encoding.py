import pandas as pd
def apply(df,context):
 cols=[c for c in context.feature_columns if df[c].dtype=="object" or str(df[c].dtype)=="bool"];before=len(context.feature_columns)
 if cols: context.working_dataframe=pd.get_dummies(df,columns=cols,dtype=float)
 context.feature_columns=[c for c in context.working_dataframe.columns if c!=context.target_column]
 return {"columns_encoded":cols,"input_feature_count":before,"output_feature_count":len(context.feature_columns),"generated_feature_names":context.feature_columns[:100]}
