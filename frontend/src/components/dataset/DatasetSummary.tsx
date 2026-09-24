import { type DatasetMetadata } from "../../services/datasetService";
export default function DatasetSummary({ dataset }: { dataset: DatasetMetadata }) {
  const cards = [["Rows", dataset.rows.toLocaleString()], ["Columns", dataset.columns.toLocaleString()], ["File Type", dataset.file_type.toUpperCase()], ["File Size", `${(dataset.file_size_bytes / 1024).toFixed(1)} KB`]];
  return <section><h2>Dataset Uploaded Successfully</h2><p>Filename: {dataset.original_filename}</p><div className="summary-grid">{cards.map(([name, value]) => <article className="summary-card" key={name}><span>{name}</span><strong>{value}</strong></article>)}</div></section>;
}
