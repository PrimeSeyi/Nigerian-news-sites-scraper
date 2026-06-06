# Nigeria Security Intelligence Dashboard

This is a modern, interactive Next.js application that visualizes geographic security intelligence across the 36 states (and the Federal Capital Territory) of Nigeria.

## How It Works

The core of the application is a highly optimized client-side SVG renderer (`InteractiveMap.tsx`). 

Instead of relying on heavy third-party mapping libraries (like Leaflet or Mapbox) or incompatible React wrappers, it directly imports raw SVG topological path data from the `@svg-maps/nigeria` module and natively maps them into React `<path>` components within a custom `viewBox`.

This provides:
1. **Zero Hydration Errors:** Fully compatible with React 19 and Next.js App Router.
2. **Instant Performance:** No external tiles to download; the map paints instantly as inline SVG.
3. **Deep Customization:** Every state is individually stylable using Tailwind CSS classes based on interaction state (`onMouseOver`, `onClick`).

## How Stats Are Displayed

Currently, the map uses a `generateStableData()` mock function to populate intelligence metrics. 

- It hashes the name of each state to generate a deterministic (stable) number of "incidents", avoiding the UI flicker that would happen with `Math.random()`.
- Based on the incident count, it assigns a `riskLevel` (`low`, `medium`, `high`) which dynamically drives the Tailwind styling logic to color the map paths (e.g., `fill-red-800/80` for high risk).
- On hover, a localized `fixed` tooltip follows your cursor showing incident counts.
- On click, a detailed "Region Profile" panel drops down below the map, revealing trends and primary threat vectors.

## How to Inject Your Own Data

To wire this dashboard to your actual database (like MongoDB or a REST API), follow these steps:

1. **Open `src/components/InteractiveMap.tsx`.**
2. Locate the `generateStableData` function and the `const stateData = useMemo(...)` hook.
3. **Replace the mock logic:**
   Instead of the synchronous mock function, you can pass data down as a prop from `page.tsx` (fetched server-side), or use `useEffect` / React Query to fetch it on the client side.
   
   ```tsx
   // Example of passing real data as props
   export default function InteractiveMap({ realData }) {
     // realData should be an object mapping state names to stats:
     // { "Lagos": { incidents: 10, riskLevel: "low", status: "Normal" }, ... }
     const stateData = realData;
     // ... rest of the component
   }
   ```
4. **Ensure Name Matching:** The keys in your data dictionary must perfectly match the SVG location names (e.g., `"Kano"`, `"Federal Capital Territory"`).

## Local Development

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.
