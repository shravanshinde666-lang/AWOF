import numpy as np
from sklearn.decomposition import PCA
def pca(df,context):
 cols=[c for c in context.feature_columns if str(df[c].dtype).startswith(("int","float"))]
 if len(cols)<2:return {"status":"skipped","reason":"PCA requires two numerical features."}
 model=PCA(n_components=.95);values=model.fit_transform(df[cols]);names=[f"pca_{i+1}" for i in range(values.shape[1])]
 context.working_dataframe=df.drop(columns=cols).assign(**{n:values[:,i] for i,n in enumerate(names)})
 context.feature_columns=[c for c in context.working_dataframe.columns if c!=context.target_column];context.artifacts["pca"]=model
 return {"components":len(names),"explained_variance_ratio":model.explained_variance_ratio_.tolist(),"cumulative_variance":float(sum(model.explained_variance_ratio_)),"input_dimensions":len(cols),"output_dimensions":len(names)}
def temporal(df,context):
 created=[]
 for c in list(context.feature_columns):
  parsed=np.array([])
  try:
   import pandas as pd;parsed=pd.to_datetime(df[c],errors="coerce")
   if parsed.notna().mean()<.8:continue
   for suffix,val in {"year":parsed.dt.year,"month":parsed.dt.month,"day":parsed.dt.day,"day_of_week":parsed.dt.dayofweek}.items():df[f"{c}_{suffix}"]=val;created.append(f"{c}_{suffix}")
  except Exception:continue
 context.working_dataframe=df;context.feature_columns=[c for c in df.columns if c!=context.target_column];return {"temporal_features":created}
