def apply(df,context):
 before=len(df);context.working_dataframe=df.drop_duplicates().copy();return {"duplicates_removed":before-len(context.working_dataframe)}
