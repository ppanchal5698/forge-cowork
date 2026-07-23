export const dynamic = "force-dynamic";

export default async function Home() {
  let status = "unreachable";
  try {
    const base = process.env.API_BASE ?? "http://localhost:8000";
    const res = await fetch(`${base}/health`, { cache: "no-store" });
    status = (await res.json()).status;
  } catch {}
  return (
    <main>
      <h1>Forge Cowork</h1>
      <p>API health: {status}</p>
    </main>
  );
}
