/* ============================================================
   Pokémon Tracker — ordenação de tabela, seleção de estado por
   carta e mostrador de total da coleção coletada.

   Tudo aqui é re-executado depois de qualquer swap do HTMX,
   porque a tabela é trocada via innerHTML em /search,
   /change-filter, /toggle_favorite, etc.
   ============================================================ */

(function () {
  "use strict";

  const STORAGE_KEY = "pokemonTracker.selectedState";

  /* ---------- estado selecionado por carta (persistido) ---------- */

  function loadSelectedStates() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) {
      return {};
    }
  }

  function saveSelectedStates(map) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
    } catch (e) {
      /* localStorage indisponível — ignora silenciosamente */
    }
  }

  let selectedStates = loadSelectedStates();

  /* ---------- parsing de preço "R$ 149,99" -> 149.99 ---------- */

  function parsePrice(raw) {
    if (raw === null || raw === undefined) return NaN;
    const cleaned = String(raw)
      .replace(/[^\d,.\-]/g, "")
      .trim();
    if (!cleaned) return NaN;

    // formato brasileiro: ponto = milhar, vírgula = decimal
    let normalized = cleaned;
    if (normalized.includes(",")) {
      normalized = normalized.replace(/\./g, "").replace(",", ".");
    }
    const value = parseFloat(normalized);
    return isNaN(value) ? NaN : value;
  }

  function formatBRL(value) {
    return (
      "R$ " +
      value.toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    );
  }

  /* ---------- estado selecionado: aplica destaque visual ---------- */

  function applyStateSelectionToRow(row) {
    const rowKey = row.dataset.rowKey;
    if (!rowKey) return;

    const chosenState = selectedStates[rowKey];
    const pills = row.querySelectorAll(".state-price-pill");

    if (!chosenState) {
      pills.forEach((pill) => {
        pill.classList.toggle("is-selected", false);
      });
    } else {
      pills.forEach((pill) => {
        pill.classList.toggle(
          "is-selected",
          chosenState && pill.dataset.stateName === chosenState,
        );
      });
    }

    // determina o preço "ativo" desta linha para fins de soma no mostrador
    let activePrice = NaN;

    if (chosenState) {
      const match = Array.from(pills).find(
        (p) => p.dataset.stateName === chosenState,
      );
      if (match) {
        activePrice = parsePrice(match.dataset.statePrice);
      }
    }

    if (isNaN(activePrice)) {
      // sem estado escolhido (ou não encontrado): usa o preço médio da variante
      const medBadge = row.querySelector(
        '.price-badge[data-price-kind="medium"]',
      );
      if (medBadge) {
        activePrice = parsePrice(medBadge.dataset.priceRaw);
      }
    }

    row.dataset.activePrice = isNaN(activePrice) ? "" : String(activePrice);
  }

  function applyStateSelectionToAllRows(root) {
    const rows = root.querySelectorAll("tr[data-row-key]");
    rows.forEach(applyStateSelectionToRow);
  }

  function onStatePillClick(event) {
    const pill = event.target.closest(".state-price-pill");
    if (!pill) return;

    const row = pill.closest("tr[data-row-key]");
    if (!row) return;

    const rowKey = row.dataset.rowKey;
    const stateName = pill.dataset.stateName;

    if (selectedStates[rowKey] === stateName) {
      // clicar de novo desmarca a seleção
      delete selectedStates[rowKey];
    } else {
      selectedStates[rowKey] = stateName;
    }

    saveSelectedStates(selectedStates);
    applyStateSelectionToRow(row);
    recomputeSummary();
  }

  /* ---------- destaque do preço base (min/med/max) clicado ---------- */

  function onPriceBadgeClick(event) {
    const badge = event.target.closest(".price-badge");
    if (!badge) return;

    const row = badge.closest("tr");
    if (!row) return;

    row.querySelectorAll(".price-badge").forEach((b) => {
      b.classList.toggle("is-selected", b === badge);
    });
  }

  /* ---------- mostrador de total da coleção coletada ---------- */

  function getRowTotals(row) {
    const minBadge = row.querySelector('.price-badge[data-price-kind="min"]');
    const medBadge = row.querySelector(
      '.price-badge[data-price-kind="medium"]',
    );
    const maxBadge = row.querySelector('.price-badge[data-price-kind="max"]');

    const rowKey = row.dataset.rowKey;
    const chosenState = rowKey ? selectedStates[rowKey] : null;

    let chosenPrice = NaN;
    if (chosenState) {
      const pill = row.querySelector(
        `.state-price-pill[data-state-name="${cssEscape(chosenState)}"]`,
      );
      if (pill) chosenPrice = parsePrice(pill.dataset.statePrice);
    }

    const minVal = isNaN(chosenPrice)
      ? parsePrice(minBadge ? minBadge.dataset.priceRaw : NaN)
      : chosenPrice;
    const medVal = isNaN(chosenPrice)
      ? parsePrice(medBadge ? medBadge.dataset.priceRaw : NaN)
      : chosenPrice;
    const maxVal = isNaN(chosenPrice)
      ? parsePrice(maxBadge ? maxBadge.dataset.priceRaw : NaN)
      : chosenPrice;

    return { minVal, medVal, maxVal };
  }

  function cssEscape(value) {
    if (window.CSS && window.CSS.escape) return window.CSS.escape(value);
    return String(value).replace(/["\\]/g, "\\$&");
  }

  function recomputeSummary() {
    const table = document.getElementById("card-table");
    const summary = document.getElementById("collection-summary");
    if (!table || !summary) return;

    const favoriteRows = Array.from(
      table.querySelectorAll("tbody tr[data-favorite='1']"),
    );

    let totalMin = 0;
    let totalMed = 0;
    let totalMax = 0;

    favoriteRows.forEach((row) => {
      const { minVal, medVal, maxVal } = getRowTotals(row);
      if (!isNaN(minVal)) totalMin += minVal;
      if (!isNaN(medVal)) totalMed += medVal;
      if (!isNaN(maxVal)) totalMax += maxVal;
    });

    const countEl = document.getElementById("summary-count");
    const minEl = document.getElementById("summary-total-min");
    const medEl = document.getElementById("summary-total-med");
    const maxEl = document.getElementById("summary-total-max");

    if (countEl) countEl.textContent = String(favoriteRows.length);
    if (minEl) minEl.textContent = formatBRL(totalMin);
    if (medEl) medEl.textContent = formatBRL(totalMed);
    if (maxEl) maxEl.textContent = formatBRL(totalMax);
  }

  /* ---------- ordenação da tabela ---------- */

  let currentSort = { key: null, type: null, direction: 1 };

  function getCellSortValue(row, key, type) {
    let raw;

    switch (key) {
      case "name":
        raw = row.dataset.name;
        break;
      case "rarity":
        raw = row.dataset.rarity;
        break;
      case "variant":
        raw = row.dataset.variant;
        break;
      case "favorite":
        raw = row.dataset.favorite;
        break;
      case "price-min": {
        const b = row.querySelector('.price-badge[data-price-kind="min"]');
        raw = b ? b.dataset.priceRaw : "";
        break;
      }
      case "price-med": {
        const b = row.querySelector('.price-badge[data-price-kind="medium"]');
        raw = b ? b.dataset.priceRaw : "";
        break;
      }
      case "price-max": {
        const b = row.querySelector('.price-badge[data-price-kind="max"]');
        raw = b ? b.dataset.priceRaw : "";
        break;
      }
      default:
        raw = "";
    }

    if (type === "number") {
      const num = parsePrice(raw);
      return isNaN(num) ? -Infinity : num;
    }

    if (type === "bool") {
      return raw === "1" ? 1 : 0;
    }

    return (raw || "").toString().toLowerCase();
  }

  function sortTable(key, type) {
    const table = document.getElementById("card-table");
    if (!table) return;

    const tbody = table.querySelector("tbody");
    if (!tbody) return;

    if (currentSort.key === key) {
      currentSort.direction *= -1;
    } else {
      currentSort = { key, type, direction: 1 };
    }

    const rows = Array.from(tbody.querySelectorAll("tr[data-row-key]"));

    rows.sort((a, b) => {
      const va = getCellSortValue(a, key, type);
      const vb = getCellSortValue(b, key, type);

      if (va < vb) return -1 * currentSort.direction;
      if (va > vb) return 1 * currentSort.direction;
      return 0;
    });

    rows.forEach((row) => tbody.appendChild(row));

    updateSortIndicators(table);
  }

  function updateSortIndicators(table) {
    table.querySelectorAll(".th-sortable").forEach((th) => {
      const indicator = th.querySelector(".sort-indicator");
      const isActive = th.dataset.sortKey === currentSort.key;
      th.classList.toggle("is-sorted", isActive);
      if (indicator) {
        indicator.textContent = isActive
          ? currentSort.direction === 1
            ? "▲"
            : "▼"
          : "";
      }
    });

    table.querySelectorAll(".sort-btn").forEach((btn) => {
      const isActive = btn.dataset.sortKey === currentSort.key;
      btn.classList.toggle("active", isActive);
      btn.classList.toggle(
        "sort-desc",
        isActive && currentSort.direction === -1,
      );
    });
  }

  function onSortableHeaderClick(event) {
    const th = event.target.closest(".th-sortable");
    if (!th) return;
    sortTable(th.dataset.sortKey, th.dataset.sortType);
  }

  function onSortButtonClick(event) {
    const btn = event.target.closest(".sort-btn");
    if (!btn) return;
    event.stopPropagation();
    sortTable(btn.dataset.sortKey, btn.dataset.sortType);
  }

  /* ---------- inicialização / re-inicialização ---------- */

  function initCardsModule(root) {
    root = root || document;

    applyStateSelectionToAllRows(root);
    recomputeSummary();

    const table =
      root.querySelector("#card-table") || root.querySelector("#card-table");
    if (table && currentSort.key) {
      // reaplica a última ordenação ativa após um swap do htmx
      const rows = Array.from(table.querySelectorAll("tbody tr[data-row-key]"));
      rows.sort((a, b) => {
        const va = getCellSortValue(a, currentSort.key, currentSort.type);
        const vb = getCellSortValue(b, currentSort.key, currentSort.type);
        if (va < vb) return -1 * currentSort.direction;
        if (va > vb) return 1 * currentSort.direction;
        return 0;
      });
      const tbody = table.querySelector("tbody");
      if (tbody) rows.forEach((row) => tbody.appendChild(row));
      updateSortIndicators(table);
    }
  }

  // delegação de eventos no document inteiro: funciona mesmo
  // depois de a tabela ser substituída pelo htmx
  document.addEventListener("click", function (event) {
    onSortableHeaderClick(event);
    onSortButtonClick(event);
    onStatePillClick(event);
    onPriceBadgeClick(event);
  });

  // sempre que o htmx troca conteúdo (busca, filtro, favoritar...),
  // recalcula seleção de estado e o mostrador de totais
  document.addEventListener("htmx:afterSwap", function (event) {
    initCardsModule(document);
  });

  document.addEventListener("DOMContentLoaded", function () {
    initCardsModule(document);
  });

  // caso o script seja carregado depois do DOM já estar pronto
  if (document.readyState !== "loading") {
    initCardsModule(document);
  }
})();
