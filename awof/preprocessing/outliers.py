from awof.profiler.outlier_detector import detect_iqr_outliers
def apply(df,context):
 return {"outliers":{c:detect_iqr_outliers(df[c]) for c in context.feature_columns if str(df[c].dtype).startswith(("int","float"))}}
