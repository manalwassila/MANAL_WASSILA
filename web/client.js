const etiquette = {
  POSITIVE: "Avis positif",
  NEGATIVE: "Avis négatif",
  INDETERMINE: "Je ne sais pas : à faire vérifier par un humain",
};

export async function analyser({ api, cle, texte, fetcher = fetch }) {
  const base = api.replace(/\/+$/, "");
  let response;
  try {
    response = await fetcher(`${base}/v1/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": cle },
      body: JSON.stringify({ text: texte }),
    });
  } catch {
    return { ok: false, message: "API injoignable : vérifiez son adresse et son état." };
  }
  const body = await response.json().catch(() => ({}));
  if (response.ok) return { ok: true, label: etiquette[body.label] ?? body.label, score: body.score };
  const erreur = body.detail?.erreur;
  if (response.status === 401) return { ok: false, message: erreur?.message ?? "Clé d’API refusée." };
  if (response.status === 403) return { ok: false, message: erreur?.message ?? "Rôle insuffisant." };
  if (response.status === 422) return { ok: false, message: "Texte invalide : saisissez entre 1 et 2000 caractères non blancs." };
  return { ok: false, message: `Erreur de l’API (${response.status}).` };
}

if (typeof document !== "undefined") {
  document.querySelector("#formulaire")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const resultat = document.querySelector("#resultat");
    resultat.textContent = "Analyse en cours…";
    const reponse = await analyser({
      api: document.querySelector("#api").value,
      cle: document.querySelector("#cle").value,
      texte: document.querySelector("#avis").value,
    });
    resultat.textContent = reponse.ok
      ? `${reponse.label} (${Math.round(reponse.score * 100)} %)`
      : reponse.message;
  });
}
