<script>
  import { onMount, tick } from "svelte";
  import * as d3 from "d3";
  import mapboxgl from "mapbox-gl";

  let allData = [];
  let filteredData = [];
  let summaryText = "";
  let coordinates = {}; // o JSON carregado

  const csvURL =
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQMswqogf1_bjVku0iKgJrsWuuUzghX7NmVoDq5UPAEMDAbBka74UmrWhbdRD7xy5JY2k-z1QhdwlGu/pub?gid=871726166&single=true&output=csv";

  async function plotMapbox(data) {
    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

    const fallbackCoord = [0, 0]; // Coordenada padrão para casos "desconhecidos"

    const map = new mapboxgl.Map({
      container: "map",
      style: "mapbox://styles/mapbox/light-v11",
      center: [0, 20],
      zoom: 1.3,
    });

    const grouped = d3.group(data, (d) => d.country.trim());

    for (const [country, entries] of grouped) {
      // Busca coordenadas ou usa fallback
      const coord = coordinates[country] || fallbackCoord;

      // Cor diferente se for coordenada genérica
      const markerColor = coord === fallbackCoord ? "#999" : "#e83e8c";

      // Cria e adiciona o marcador
      // Cria um elemento HTML customizado para o marcador
      const el = document.createElement("div");
      el.style.width = "32px";
      el.style.height = "32px";
      el.style.backgroundColor = markerColor;
      el.style.borderRadius = "50%";
      el.style.display = "flex";
      el.style.justifyContent = "center";
      el.style.alignItems = "center";
      el.style.color = "white";
      el.style.fontSize = "14px";
      el.style.fontWeight = "bold";
      el.style.border = "2px solid white";
      el.style.boxShadow = "0 0 5px #00000088";
      el.innerText = entries.length; // <-- Aqui o número de entradas

      // Usa esse elemento no marcador
      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat(coord)
        .setPopup(
          new mapboxgl.Popup().setHTML(`
      <strong>${country}</strong><br>
      ${entries.length} links<br>
      ${coord === fallbackCoord ? "<em>Localização desconhecida</em><br>" : ""}
      <button onclick='window.selectCountry("${country}")'>
      See data
      </button>

    `),
        )
        .addTo(map);
    }

    // Função acessível globalmente
    window.selectCountry = (country) => {
      updateTable(country);
    };

    // Listener global (como já estava)
    window.addEventListener("select-country", (e) => {
      updateTable(e.detail);
    });
  }

  function updateTable(country) {
    filteredData = allData.filter(
      (row) => row.country.trim() === country.trim(),
    );
    filteredData = [...filteredData]; // 🔥 força a reatividade no Svelte
  }

  function displayEntryInfo(data) {
    const numRows = data.length;
    const earliestDate = data.reduce(
      (min, row) => (row.date < min ? row.date : min),
      data[0].date,
    );
    const latestDate = data.reduce(
      (max, row) => (row.date > max ? row.date : max),
      data[0].date,
    );
    summaryText = `${numRows} entries in BioArt from ${earliestDate} to ${latestDate}`;
  }

  onMount(async () => {
    coordinates = await d3.json("countryCoordinates.json");
    allData = await d3.csv(csvURL);
    filteredData = allData;
    displayEntryInfo(allData);
    await tick();
    console.log(document.getElementById("map")); // deve retornar <div id="map">
    await plotMapbox(allData);
  });
</script>

<div class="container pt-5">
<h2 class="py-5 text-center">{summaryText}</h2>
<div id="map"></div>
</div>

<div class="container pb-5">
<table id="data-table" class="table table-striped">
  <thead>
    <tr>
      <th>Date</th>
      <th>Country</th>
      <th>Link</th>
      <th>Summary</th>
    </tr>
  </thead>
  <tbody>
    {#each filteredData as row}
      <tr>
        <td>{row.date}</td>
        <td>{row.country}</td>
        <td><a href={row.link} target="_blank">Link</a></td>
        <td>{row.summary}</td>
      </tr>
    {/each}
  </tbody>
</table>
</div>

<style>
  #map {
    width: 100%;
    height: 600px;
    border-radius: 12px;
    margin-bottom: 2rem;
  }
</style>
