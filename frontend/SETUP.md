# Frontend Setup Guide: Tailwind CSS v4 + shadcn + Vite

## Why this guide exists

If you set up a Vite + React + TypeScript project, then try to add Tailwind CSS v4 and shadcn, you'll find yourself editing **four different config files** for what feels like it should be one thing. The Tailwind docs don't explain the shadcn parts. The shadcn docs gloss over the *why*. This guide explains **who reads each config file, why it's needed, and how they all fit together**.

The stack:

```
vite v7          - bundler / dev server
tailwindcss v4   - CSS framework
@tailwindcss/vite - Vite plugin for Tailwind v4
typescript ~5.9  - type checker (NOT a bundler)
shadcn           - component library that generates source files using @/ imports
```

---

## 1. `@import "tailwindcss"` in index.css

### The file

```css
/* src/index.css */
@import "tailwindcss";
```

### Who reads it

The **`@tailwindcss/vite` plugin**, running inside Vite's dev server and build pipeline.

### Why it's needed

Tailwind CSS v4 completely changed how it discovers that your project uses Tailwind. In v3, you had a `tailwind.config.js` file and three directives in your CSS:

```css
/* Tailwind v3 (old way) */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

In v4, all of that is replaced by a single CSS import:

```css
/* Tailwind v4 (new way) */
@import "tailwindcss";
```

This is not a cosmetic change. It reflects a fundamental architectural shift:

- **v3** used a PostCSS plugin that looked for a `tailwind.config.js` file, read your `content` paths from it, scanned your source files for class names, and injected generated CSS in place of the `@tailwind` directives.
- **v4** is CSS-native. The `@import "tailwindcss"` statement is a real CSS import. The `@tailwindcss/vite` plugin intercepts it during Vite's CSS processing pipeline, uses it as the entry point, then scans your source files for utility classes and generates the corresponding CSS. Configuration that used to live in `tailwind.config.js` (theme, colors, etc.) now lives in CSS itself using `@theme` blocks.

### How it works step by step

1. Your `main.tsx` imports `./index.css`.
2. Vite sees a CSS import and runs it through its CSS pipeline.
3. The `@tailwindcss/vite` plugin (registered in `vite.config.ts` as `tailwindcss()`) intercepts the file.
4. It finds `@import "tailwindcss"` and treats this as "Tailwind is active in this CSS file."
5. It scans all files included by Vite's module graph for utility class names (`flex`, `p-4`, `bg-blue-500`, etc.).
6. It generates the corresponding CSS and injects it into the output.

### Why shadcn couldn't find Tailwind without it

When you run `npx shadcn@latest init`, shadcn checks whether Tailwind is set up. In v4, it looks for `@import "tailwindcss"` in your CSS files. If your `index.css` is empty or still has the v3 `@tailwind` directives, shadcn's init will either fail or warn that Tailwind isn't detected.

---

## 2. `baseUrl` + `paths` in tsconfig.json and tsconfig.app.json

### The files

```jsonc
// tsconfig.json (root)
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ],
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

```jsonc
// tsconfig.app.json (app source config)
{
  "compilerOptions": {
    // ... other options ...
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
```

### Who reads what

This is the confusing part: there are **two tsconfig files with the same paths config**, and they're read by **different tools**.

#### tsconfig.json (root)

- **Read by**: Your IDE (VS Code / WebStorm), ESLint, and any tool that looks for `tsconfig.json` by default.
- **Does NOT compile anything**. Notice `"files": []` -- it includes zero files directly.
- **Purpose**: Acts as a hub. It uses TypeScript's [project references](https://www.typescriptlang.org/docs/handbook/project-references.html) to point to the real configs (`tsconfig.app.json` for your React source, `tsconfig.node.json` for `vite.config.ts`).
- **Why paths are here**: Some tools (notably VS Code's TypeScript language service in certain configurations, and some ESLint setups) read `tsconfig.json` directly. Without the `paths` mapping here, your editor might show red squiggles on `@/` imports even though compilation works fine.

#### tsconfig.app.json

- **Read by**: `tsc -b` (the TypeScript compiler, invoked by `npm run build`).
- **This is the one that actually type-checks your `src/` code.** Look at the `"include": ["src"]` field.
- **Why paths are here**: This is where they *actually matter* for type checking. When `tsc` encounters `import { cn } from "@/lib/utils"`, it consults `compilerOptions.paths` to resolve `@/lib/utils` to `./src/lib/utils`. Without this, `tsc` would report: `Cannot find module '@/lib/utils'`.

#### tsconfig.node.json

- **Read by**: `tsc -b` for Node-side files.
- **Scope**: Only includes `vite.config.ts`. This file runs in Node, not the browser, so it gets its own config with Node-appropriate settings.
- **No paths needed**: `vite.config.ts` never imports from `@/...`.

### What `paths` actually does (and does NOT do)

`paths` tells TypeScript's **type checker**: "when you see an import starting with `@/`, look for the corresponding file under `./src/`."

```
Import:  @/components/ui/button
         ↓ paths resolution
File:    ./src/components/ui/button.tsx
```

Critically: **TypeScript does not transform or rewrite these imports.** In this project, `tsc` runs with `"noEmit": true` -- it doesn't even produce output files. It only checks types. The `paths` mapping exists solely so `tsc` can find the right type declarations for each `@/` import and verify that your types are correct.

This means `paths` alone does NOT make your app work at runtime. You need Vite to resolve these imports too (next section).

### Why both files need it

```
┌─────────────────────────────────────────────────┐
│  VS Code opens project                          │
│  → finds tsconfig.json                          │
│  → reads compilerOptions.paths                  │
│  → resolves @/ imports in the editor            │
│  → no red squiggles                             │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  npm run build  →  tsc -b                       │
│  → reads tsconfig.json references               │
│  → follows reference to tsconfig.app.json       │
│  → uses tsconfig.app.json's compilerOptions     │
│  → reads paths from tsconfig.app.json           │
│  → resolves @/ imports for type checking        │
│  → no type errors                               │
└─────────────────────────────────────────────────┘
```

With project references, `tsc -b` does **not** inherit `compilerOptions` from the root `tsconfig.json`. Each referenced project is self-contained. So even though the root has `paths`, `tsconfig.app.json` needs its own copy. Remove it from `tsconfig.app.json` and `tsc -b` breaks. Remove it from `tsconfig.json` and your editor breaks.

---

## 3. `resolve.alias` in vite.config.ts

### The file

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

### Who reads it

**Vite** -- the bundler and dev server. This is the tool that actually resolves `import` statements, finds the files on disk, and bundles them into your application.

### Why it's needed SEPARATELY from tsconfig paths

This is the key insight that confuses people: **TypeScript and Vite are two completely separate tools that both need to resolve your imports, independently, for different reasons.**

| Tool | Purpose | Reads config from | What it does with `@/` |
|------|---------|-------------------|----------------------|
| `tsc` | Type checking | `tsconfig.app.json` `paths` | Finds type information. Verifies your code is type-safe. Produces no output. |
| Vite | Bundling | `vite.config.ts` `resolve.alias` | Finds the actual file on disk. Reads its contents. Bundles it into the app. |

They solve the **same problem** (resolving `@/components/ui/button` to `./src/components/ui/button`) for **different tools** at **different stages**:

```
                    Your source code
                    import { Button } from "@/components/ui/button"
                           │
              ┌────────────┴────────────┐
              │                         │
         Type checking              Bundling
              │                         │
        ┌─────┴──────┐           ┌──────┴──────┐
        │ tsc -b     │           │ vite dev    │
        │            │           │ vite build  │
        │ reads:     │           │             │
        │ tsconfig   │           │ reads:      │
        │ .app.json  │           │ vite.config │
        │ paths      │           │ .ts alias   │
        └─────┬──────┘           └──────┬──────┘
              │                         │
        Resolves types            Resolves files
        "Are the props             "What is the
         correct?"                  actual code?"
              │                         │
        ✓ No type errors          ✓ Bundle works
```

### What happens if you only configure one

- **paths in tsconfig but NOT alias in vite.config.ts**: `tsc` is happy (types resolve), but `vite dev` throws `[vite] Internal server error: Failed to resolve import "@/components/ui/button"`. Your app doesn't start.

- **alias in vite.config.ts but NOT paths in tsconfig**: Vite runs fine (app works in browser), but `tsc` reports `error TS2307: Cannot find module '@/components/ui/button'`. Your `npm run build` fails because the build script runs `tsc -b && vite build` (type check first, then bundle).

You need both.

---

## 4. Why the Tailwind docs don't mention any of this

The Tailwind v4 docs cover exactly one thing from this guide: the `@import "tailwindcss"` line. That's the only part that's Tailwind's responsibility. The docs tell you to add it and explain what it does. If you follow the [Tailwind v4 + Vite installation guide](https://tailwindcss.com/docs/installation/vite), you'll see it there -- but it's easy to miss if you skip ahead or are coming from v3 muscle memory.

The path alias configuration (`@/*` in tsconfig and vite.config.ts) has **nothing to do with Tailwind**. It's a requirement of **shadcn**.

Here's why: when you run `npx shadcn@latest init` and then add components like `npx shadcn@latest add button`, shadcn generates source files directly into your project. Those generated files contain imports like:

```tsx
// This is generated code from shadcn, placed at src/components/ui/button.tsx
import { cn } from "@/lib/utils"
```

shadcn hardcodes the `@/` prefix in its generated code. It expects you to have a path alias where `@` maps to your source root. This is a shadcn convention, not a Tailwind convention and not a Vite convention. Tailwind doesn't care how you import your components. Vite doesn't care either until you tell it about the alias.

So the full picture of "who is responsible for what documentation" is:

| Config | Whose responsibility | Where it's documented |
|--------|---------------------|-----------------------|
| `@import "tailwindcss"` | Tailwind v4 | Tailwind docs (installation guide) |
| `@tailwindcss/vite` plugin | Tailwind v4 | Tailwind docs (Vite framework guide) |
| `paths` in tsconfig | TypeScript + shadcn | shadcn docs (installation) |
| `resolve.alias` in vite.config | Vite + shadcn | shadcn docs (installation) |

The shadcn docs do walk you through setting up path aliases. But if you're going back and forth between the Tailwind docs and your terminal, it's easy to wonder "why didn't the Tailwind docs mention this?" The answer: because it's not their problem.

---

## 5. The full picture: data flow for a single import

Let's trace what happens when your code contains:

```tsx
import { Button } from "@/components/ui/button"
```

and that `Button` component uses Tailwind classes:

```tsx
// src/components/ui/button.tsx
export function Button({ children }) {
  return <button className="px-4 py-2 bg-blue-500 text-white rounded">{children}</button>
}
```

### Phase 1: Type checking (`tsc -b`)

Triggered by: `npm run build` (which runs `tsc -b && vite build`)

```
1. tsc reads tsconfig.json
2. tsconfig.json has references → follows to tsconfig.app.json
3. tsconfig.app.json says include: ["src"]
4. tsc finds your source file with: import { Button } from "@/components/ui/button"
5. tsc consults compilerOptions.paths:  "@/*" → ["./src/*"]
6. tsc resolves "@/components/ui/button" → "./src/components/ui/button.tsx"
7. tsc reads that file, checks that Button is exported, checks prop types, etc.
8. Result: ✓ no type errors (or errors if your types are wrong)
9. tsc produces NO output files (noEmit: true). Its only job was checking.
```

### Phase 2: Bundling (`vite build` or `vite dev`)

Triggered by: `npm run build` (after tsc passes) or `npm run dev`

```
1. Vite reads vite.config.ts
2. Vite starts from index.html → finds main.tsx → begins building the module graph
3. Vite encounters: import { Button } from "@/components/ui/button"
4. Vite consults resolve.alias:  "@" → "/absolute/path/to/src"
5. Vite resolves "@/components/ui/button" → "/absolute/path/to/src/components/ui/button.tsx"
6. Vite reads that file, transforms JSX via @vitejs/plugin-react-swc
7. Vite adds it to the bundle (dev: serves via HMR; build: writes to dist/)
8. Result: ✓ the Button component is included in your app
```

### Phase 3: CSS processing (`@tailwindcss/vite`)

Runs as part of Phase 2, but specifically for CSS.

```
1. Vite encounters: import './index.css' in main.tsx
2. Vite runs index.css through its CSS pipeline
3. The @tailwindcss/vite plugin intercepts, finds @import "tailwindcss"
4. The plugin scans all modules in Vite's module graph (including button.tsx)
5. It finds class names: "px-4", "py-2", "bg-blue-500", "text-white", "rounded"
6. It generates the CSS rules for exactly those utility classes
7. The generated CSS is injected into the page (dev: <style> tag via HMR; build: .css file in dist/)
8. Result: ✓ the Button renders with correct styles
```

### All three phases, visualized

```
┌──────────────────────────────────────────────────────────────────┐
│                        Your Source Code                          │
│  import { Button } from "@/components/ui/button"                │
│  <Button>Click me</Button>                                      │
└──────────────────┬──────────────────┬───────────────────┬────────┘
                   │                  │                   │
          ┌────────▼────────┐  ┌──────▼───────┐  ┌───────▼───────┐
          │   TypeScript    │  │    Vite      │  │  Tailwind     │
          │   (tsc -b)      │  │   Bundler    │  │  CSS Plugin   │
          ├─────────────────┤  ├──────────────┤  ├───────────────┤
          │ Config:         │  │ Config:      │  │ Config:       │
          │ tsconfig.app    │  │ vite.config  │  │ index.css     │
          │ .json paths     │  │ .ts alias    │  │ @import       │
          ├─────────────────┤  ├──────────────┤  ├───────────────┤
          │ Input:          │  │ Input:       │  │ Input:        │
          │ @/ import       │  │ @/ import    │  │ class names   │
          │                 │  │              │  │ in JSX        │
          ├─────────────────┤  ├──────────────┤  ├───────────────┤
          │ Output:         │  │ Output:      │  │ Output:       │
          │ Type errors     │  │ JS bundle    │  │ CSS with      │
          │ (or none)       │  │ in dist/     │  │ utility rules │
          └─────────────────┘  └──────────────┘  └───────────────┘
```

---

## Summary: every config file and its reader

| File | Read by | Purpose |
|------|---------|---------|
| `src/index.css` | `@tailwindcss/vite` plugin (inside Vite) | `@import "tailwindcss"` activates Tailwind's CSS generation |
| `tsconfig.json` | VS Code, ESLint, IDE tooling | Path aliases for editor intellisense; project reference hub |
| `tsconfig.app.json` | `tsc -b` (TypeScript compiler) | Path aliases + all compiler options for type-checking `src/` |
| `tsconfig.node.json` | `tsc -b` (TypeScript compiler) | Compiler options for `vite.config.ts` (Node context, no aliases needed) |
| `vite.config.ts` | Vite dev server + build | Path aliases for actual module resolution at bundle time; plugin registration |
| `package.json` | npm, Vite, everything | Dependencies, scripts (`"build": "tsc -b && vite build"` -- note the two-step pipeline) |

The reason this feels like unnecessary duplication is because **two separate tools** (TypeScript and Vite) **both need to resolve the same import paths**, and neither reads the other's config. TypeScript doesn't read `vite.config.ts`. Vite doesn't read `tsconfig.json` (at least not for path resolution by default). So you tell each tool separately.

This is the cost of a toolchain where the type checker and the bundler are independent programs. It's explicit, and once you understand it, it's predictable.
