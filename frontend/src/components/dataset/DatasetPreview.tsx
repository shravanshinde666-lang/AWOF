import { type DatasetMetadata } from "../../services/datasetService";
export default function DatasetPreview({ dataset }: { dataset: DatasetMetadata }) {
  return <section><h2>Dataset Preview</h2><div className="table-scroll"><table><thead><tr>{dataset.column_names.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{dataset.preview.map((row, index) => <tr key={index}>{dataset.column_names.map((column) => <td key={column}>{row[column] == null ? "—" : String(row[column])}</td>)}</tr>)}</tbody></table></div></section>;
}
