import { DiffEditor } from '@monaco-editor/react'

interface Props {
  diff: string
}

function parseDiff(unified: string): { original: string; modified: string } {
  const lines = unified.split('\n')
  const original: string[] = []
  const modified: string[] = []

  for (const line of lines) {
    if (line.startsWith('---') || line.startsWith('+++') || line.startsWith('@@')) continue
    if (line.startsWith('-')) {
      original.push(line.slice(1))
    } else if (line.startsWith('+')) {
      modified.push(line.slice(1))
    } else {
      original.push(line.slice(1))
      modified.push(line.slice(1))
    }
  }

  return { original: original.join('\n'), modified: modified.join('\n') }
}

export default function DiffViewer({ diff }: Props) {
  if (!diff) return null
  const { original, modified } = parseDiff(diff)

  return (
    <div className="bg-white rounded-xl shadow overflow-hidden">
      <div className="px-4 py-2 border-b text-sm font-medium text-gray-600">Config Diff</div>
      <DiffEditor
        height="400px"
        language="plaintext"
        original={original}
        modified={modified}
        options={{ readOnly: true, renderSideBySide: true, minimap: { enabled: false }, fontSize: 12 }}
      />
    </div>
  )
}
