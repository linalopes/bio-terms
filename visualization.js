// Fetch the CSV data and initialize the visualization
document.addEventListener('DOMContentLoaded', function() {
  // Define the colors from the CSS variables
  const mapFillColor = getComputedStyle(document.documentElement).getPropertyValue('--bs-turquoise');
  const mapStrokeColor = getComputedStyle(document.documentElement).getPropertyValue('--bs-deep-purple');
  const circleFillColor = getComputedStyle(document.documentElement).getPropertyValue('--bs-pink');

  // Load CSV and process the map and table
  loadCSVData();

  let allData;  // Store all CSV data globally

  async function loadCSVData() {
      const csvURL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQMswqogf1_bjVku0iKgJrsWuuUzghX7NmVoDq5UPAEMDAbBka74UmrWhbdRD7xy5JY2k-z1QhdwlGu/pub?gid=1264427414&single=true&output=csv';
      const response = await fetch(csvURL);
      const data = await response.text();

      // Parse CSV using PapaParse
      Papa.parse(data, {
          header: true,
          skipEmptyLines: true,
          complete: function(results) {
              allData = results.data;  // Store data for later use
              plotMap(allData);  // Pass full data to the map plotter
              populateTable(allData);  // Populate table initially with all data
              displayEntryInfo(allData);  // Display summary info
          }
      });
  }

  // Plot the map using D3.js
  function plotMap(data) {
    const aspectRatio = 960 / 600;  // Define the aspect ratio (width/height)

      const svg = d3.select("#map")
          .append("svg")
          .attr("width", "100%")
          .attr("height", function() {
            const width = document.querySelector("#map").offsetWidth;
            return width / aspectRatio;
        })
        .attr("viewBox", `0 0 960 600`)
        .attr("preserveAspectRatio", "xMidYMid meet");

      const projection = d3.geoNaturalEarth1()
          .scale(150)
          .translate([480, 300]);

      const path = d3.geoPath().projection(projection);

      // Add a div element for the tooltip
      const tooltip = d3.select("body")
        .append("div")
        .attr("class", "tooltip")
        .style("position", "absolute")
        .style("padding", "8px")
        .style("background", "lightgray")
        .style("border-radius", "5px")
        .style("pointer-events", "none")
        .style("opacity", 0);  // Initially hidden

      // Load GeoJSON world data to draw the map
      d3.json("https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson").then(function(geoData) {
          svg.append("g")
              .selectAll("path")
              .data(geoData.features)
              .enter()
              .append("path")
              .attr("d", path)
              .attr("fill", mapFillColor)
              .attr("stroke", mapStrokeColor)
              .attr("stroke-width", 1);

          // Group data by country from CSV
          const countryLinks = d3.group(data, d => d['country']);

          // Prepare data to map the number of links per country
          const countryData = Array.from(countryLinks, ([key, value]) => ({
              country: key,
              count: value.length,
              links: value.map(d => ({ date: d['date'], link: d['link'], summary: d['summary'] })) // Use link data
          }));

          // Plot circles for each country based on the count of BioArt links
          svg.selectAll("circle")
              .data(countryData)
              .enter()
              .append("circle")
              .attr("class", "circle")
              .attr("cx", d => {
                  const countryFeature = geoData.features.find(f => f.properties.name === d.country);
                  if (countryFeature) {
                      const coordinates = projection(d3.geoCentroid(countryFeature));
                      return coordinates ? coordinates[0] : null;
                  }
                  return null;
              })
              .attr("cy", d => {
                  const countryFeature = geoData.features.find(f => f.properties.name === d.country);
                  if (countryFeature) {
                      const coordinates = projection(d3.geoCentroid(countryFeature));
                      return coordinates ? coordinates[1] : null;
                  }
                  return null;
              })
              .attr("r", d => d.count > 0 ? Math.sqrt(d.count) * 5 : 0) // Circle radius based on the count
              .attr("fill", circleFillColor)
              .attr("stroke", "white")
              .attr("stroke-width", 0.5)
              .attr("opacity", 0.8)
              .on("mouseover", function(event, d) {
                  // Show tooltip on hover
                  tooltip.transition().duration(200).style("opacity", 1);
                  tooltip.html(`Country: ${d.country}<br/>Links: ${d.count}`)
                      .style("left", (event.pageX + 5) + "px")
                      .style("top", (event.pageY - 28) + "px");
              })
              .on("mouseout", function() {
                  // Hide tooltip
                  tooltip.transition().duration(500).style("opacity", 0);
              })
              .on("click", function(event, d) {
                  // Instead of displaying in tooltip, update the table with the country's links
                  updateTable(d.country);
              });
      });
  }

  // Populate the table with CSV data initially
  function populateTable(data) {
      const tableBody = document.querySelector('#data-table tbody');
      tableBody.innerHTML = ''; // Clear existing rows
      data.forEach(row => {
          const newRow = `<tr>
              <td>${row.date}</td>
              <td>${row.country}</td>
              <td><a href="${row.link}" target="_blank">Link</a></td>
              <td>${row.summary}</td>
          </tr>`;
          tableBody.innerHTML += newRow;
      });
  }

  // Update the table with country-specific data when a circle is clicked
  function updateTable(country) {
      const tableBody = document.querySelector('#data-table tbody');
      tableBody.innerHTML = ''; // Clear current table

      // Filter the global data to get the rows for the clicked country
      const countryData = allData.filter(row => row.country === country);

      // Populate the table with the filtered country data
      countryData.forEach(row => {
          const newRow = `<tr>
              <td>${row.date}</td>
              <td>${row.country}</td>
              <td><a href="${row.link}" target="_blank">Link</a></td>
              <td>${row.summary}</td>
          </tr>`;
          tableBody.innerHTML += newRow;
      });
  }

  // Display the number of entries and date range
  function displayEntryInfo(data) {
      const dateRange = document.querySelector('#map-section h2');
      const numRows = data.length;
      const earliestDate = data.reduce((min, row) => row.date < min ? row.date : min, data[0].date);
      const latestDate = data.reduce((max, row) => row.date > max ? row.date : max, data[0].date);

      dateRange.textContent = `${numRows} entries in BioArt from ${earliestDate} to ${latestDate}`;
  }
});
