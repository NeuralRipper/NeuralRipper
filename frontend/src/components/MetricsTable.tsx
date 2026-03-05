import { useState } from "react"
import {
    useReactTable,
    getCoreRowModel,
    getSortedRowModel,
    flexRender,
    type ColumnDef,
    type SortingState,
} from "@tanstack/react-table"
import {
    Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from "@/components/ui/table"
import type { InferenceResultResponse } from "@/types"

interface MetricsRow {
    name: string
    result: InferenceResultResponse
}

const columns: ColumnDef<MetricsRow>[] = [
    { accessorFn: r => r.name, id: "model", header: "Model" },
    {
        accessorFn: r => r.result.ttft_ms, id: "ttft", header: "TTFT (ms)",
        cell: ({ getValue }) => fmtNum(getValue<number | null>(), 0)
    },
    {
        accessorFn: r => r.result.tpot_ms, id: "tpot", header: "TPOT (ms)",
        cell: ({ getValue }) => fmtNum(getValue<number | null>(), 1)
    },
    {
        accessorFn: r => r.result.tokens_per_second, id: "speed", header: "Speed (tok/s)",
        cell: ({ getValue }) => fmtNum(getValue<number | null>(), 1)
    },
    {
        accessorFn: r => r.result.e2e_latency_ms, id: "e2e", header: "E2E (ms)",
        cell: ({ getValue }) => fmtNum(getValue<number | null>(), 0)
    },
    {
        accessorFn: r => r.result.gpu_utilization_pct, id: "gpu", header: "GPU (%)",
        cell: ({ getValue }) => fmtNum(getValue<number | null>(), 0)
    },
    {
        accessorFn: r => r.result.gpu_memory_used_mb, id: "vram", header: "VRAM (MB)",
        cell: ({ getValue }) => fmtNum(getValue<number | null>(), 0)
    },
]

function fmtNum(v: number | null | undefined, decimals: number): string {
    return v != null ? v.toFixed(decimals) : "-"
}

export default function MetricsTable({ rows }: { rows: MetricsRow[] }) {
    const [sorting, setSorting] = useState<SortingState>([])

    const table = useReactTable({
        data: rows,
        columns,
        state: { sorting },
        onSortingChange: setSorting,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
    })

    if (rows.length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
                Metrics appear here when models complete.
            </div>
        )
    }

    return (
        <Table>
            <TableHeader>
                {table.getHeaderGroups().map(hg => (
                    <TableRow key={hg.id}>
                        {hg.headers.map(header => (
                            <TableHead
                                key={header.id}
                                className="cursor-pointer select-none text-xs"
                                onClick={header.column.getToggleSortingHandler()}
                            >
                                {flexRender(header.column.columnDef.header, header.getContext())}
                                {{ asc: " ▲", desc: " ▼" }[header.column.getIsSorted() as string] ?? ""}
                            </TableHead>
                        ))}
                    </TableRow>
                ))}
            </TableHeader>
            <TableBody>
                {table.getRowModel().rows.map(row => (
                    <TableRow key={row.id}>
                        {row.getVisibleCells().map(cell => (
                            <TableCell key={cell.id} className="text-xs">
                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </TableCell>
                        ))}
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    )
}
