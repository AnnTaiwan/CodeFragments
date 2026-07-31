const listUrlPattern = /^https:\/\/letterboxd\.com\/([^/]+)\/list\/([^/]+)\/?$/;

const state = {
  films: [],
  gameSize: 0,
  currentWinner: null,
  challenger: null,
  currentWinnerSide: null,
  remaining: [],
  path: [],
  comparisonNumber: 0,
};

const elements = {
  notice: document.querySelector("#notice"),
  newListButton: document.querySelector("#new-list-button"),
  loadPanel: document.querySelector("#load-panel"),
  setupPanel: document.querySelector("#setup-panel"),
  gamePanel: document.querySelector("#game-panel"),
  resultPanel: document.querySelector("#result-panel"),
  urlForm: document.querySelector("#url-form"),
  listUrl: document.querySelector("#list-url"),
  loadedCount: document.querySelector("#loaded-count"),
  sizeForm: document.querySelector("#size-form"),
  gameSize: document.querySelector("#game-size"),
  progress: document.querySelector("#progress"),
  fieldSizeStat: document.querySelector("#field-size-stat"),
  leftRoleStat: document.querySelector("#left-role-stat"),
  rightRoleStat: document.querySelector("#right-role-stat"),
  leftChoice: document.querySelector("#left-choice"),
  rightChoice: document.querySelector("#right-choice"),
  winnerCard: document.querySelector("#winner-card"),
  pathList: document.querySelector("#path-list"),
  playAgainButton: document.querySelector("#play-again-button"),
};

let displayed = { left: null, right: null };

elements.urlForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const url = elements.listUrl.value.trim();

  if (!listUrlPattern.test(url)) {
    showNotice("Enter a Letterboxd list URL like https://letterboxd.com/ChouAnn/list/2026/");
    return;
  }

  await fetchFilms(url);
});

elements.sizeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const size = Number.parseInt(elements.gameSize.value, 10);
  await startGame(size);
});

elements.leftChoice.addEventListener("click", () => choose(displayed.left));
elements.rightChoice.addEventListener("click", () => choose(displayed.right));
elements.playAgainButton.addEventListener("click", async () => startGame(state.gameSize));
elements.newListButton.addEventListener("click", resetToListInput);

document.addEventListener("keydown", (event) => {
  if (elements.gamePanel.classList.contains("hidden")) {
    return;
  }

  if (event.key === "ArrowLeft") {
    choose(displayed.left);
  }

  if (event.key === "ArrowRight") {
    choose(displayed.right);
  }
});

async function fetchFilms(url) {
  clearNotice();
  setLoading(true);

  try {
    const response = await fetch("/api/letterboxd-list", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Could not fetch this Letterboxd list.");
    }

    state.films = payload.films;
    clearNotice();
    showSetup();
  } catch (error) {
    showNotice(error.message || "Could not fetch this Letterboxd list.");
  } finally {
    setLoading(false);
  }
}

function setLoading(isLoading) {
  const submitButton = elements.urlForm.querySelector("button");
  submitButton.disabled = isLoading;
  elements.listUrl.disabled = isLoading;
  submitButton.textContent = isLoading ? "Fetching..." : "Fetch";

  if (isLoading) {
    showNotice("Fetching films from Letterboxd...");
  }
}

function showSetup() {
  if (state.films.length < 2) {
    showNotice("This list needs at least 2 films.");
    return;
  }

  elements.loadPanel.classList.add("hidden");
  elements.setupPanel.classList.remove("hidden");
  elements.resultPanel.classList.add("hidden");
  elements.newListButton.classList.remove("hidden");
  elements.loadedCount.textContent = `Loaded ${state.films.length} films.`;
  elements.gameSize.max = String(state.films.length);
  elements.gameSize.value = state.gameSize ? String(state.gameSize) : "";
  elements.gameSize.focus();
}

async function startGame(size) {
  if (!Number.isInteger(size) || size < 2 || size > state.films.length) {
    showNotice(`This list has ${state.films.length} films. Choose a number from 2 to ${state.films.length}.`);
    return;
  }

  clearNotice();
  state.gameSize = size;
  const field = sample(state.films, size);
  await enrichPosters(field);
  state.currentWinner = drawOne(field);
  state.challenger = drawOne(field);
  state.currentWinnerSide = null;
  state.remaining = field;
  state.path = [];
  state.comparisonNumber = 1;

  elements.setupPanel.classList.add("hidden");
  elements.resultPanel.classList.add("hidden");
  elements.gamePanel.classList.remove("hidden");
  renderComparison();
}

async function enrichPosters(films) {
  showNotice("Fetching posters for this game...");

  try {
    const response = await fetch("/api/posters", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ films }),
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Could not fetch posters.");
    }

    for (const film of films) {
      film.posterUrl = payload.posters[film.url] || null;
    }

    clearNotice();
  } catch (error) {
    for (const film of films) {
      film.posterUrl = null;
    }
    showNotice("Could not fetch some posters. Continuing without missing posters.");
  }
}

function choose(winner) {
  if (!winner || !state.currentWinner || !state.challenger) {
    return;
  }

  const loser = winner === state.currentWinner ? state.challenger : state.currentWinner;
  state.path.push({ winner, loser });
  state.currentWinnerSide = winner === displayed.left ? "left" : "right";
  state.currentWinner = winner;

  if (state.remaining.length === 0) {
    showResult();
    return;
  }

  state.challenger = drawOne(state.remaining);
  state.comparisonNumber += 1;
  renderComparison();
}

function renderComparison() {
  elements.progress.textContent = `Choice ${state.comparisonNumber} of ${state.gameSize - 1}`;
  elements.fieldSizeStat.textContent = String(state.gameSize);

  if (!state.currentWinnerSide) {
    const pair = shuffle([state.currentWinner, state.challenger]);
    displayed = { left: pair[0], right: pair[1] };
  } else if (state.currentWinnerSide === "left") {
    displayed = { left: state.currentWinner, right: state.challenger };
  } else {
    displayed = { left: state.challenger, right: state.currentWinner };
  }

  renderSeatRoles();
  renderFilmChoice(elements.leftChoice, displayed.left);
  renderFilmChoice(elements.rightChoice, displayed.right);
}

function renderSeatRoles() {
  const leftIsWinner = displayed.left === state.currentWinner;
  const rightIsWinner = displayed.right === state.currentWinner;
  elements.leftRoleStat.textContent = leftIsWinner ? "Winner" : "New";
  elements.rightRoleStat.textContent = rightIsWinner ? "Winner" : "New";
  elements.leftChoice.dataset.role = leftIsWinner ? "Current winner" : "New challenger";
  elements.rightChoice.dataset.role = rightIsWinner ? "Current winner" : "New challenger";
}

function showResult() {
  elements.gamePanel.classList.add("hidden");
  elements.resultPanel.classList.remove("hidden");
  renderFilmCard(elements.winnerCard, state.currentWinner);
  elements.pathList.replaceChildren(
    ...state.path.map((matchup, index) => {
      const item = document.createElement("li");
      const round = document.createElement("span");
      round.className = "path-round";
      round.textContent = `Choice ${index + 1}`;

      const copy = document.createElement("span");
      copy.className = "path-copy";
      copy.textContent = `${filmLabel(matchup.winner)} beat ${filmLabel(matchup.loser)}`;

      item.append(round, copy);
      return item;
    }),
  );
}

function resetToListInput() {
  state.films = [];
  state.gameSize = 0;
  state.currentWinner = null;
  state.challenger = null;
  state.currentWinnerSide = null;
  state.remaining = [];
  state.path = [];
  state.comparisonNumber = 0;
  displayed = { left: null, right: null };

  clearNotice();
  elements.listUrl.value = "";
  elements.loadPanel.classList.remove("hidden");
  elements.setupPanel.classList.add("hidden");
  elements.gamePanel.classList.add("hidden");
  elements.resultPanel.classList.add("hidden");
  elements.newListButton.classList.add("hidden");
  elements.listUrl.focus();
}

function renderFilmChoice(button, film) {
  button.replaceChildren();
  const role = document.createElement("span");
  role.className = "seat-label";
  role.textContent = button.dataset.role || "";

  const card = document.createElement("div");
  card.className = "film-card";
  renderFilmCard(card, film);
  button.append(role, card);
}

function renderFilmCard(container, film) {
  container.replaceChildren();

  const poster = document.createElement("div");
  poster.className = "poster-frame";

  if (film.posterUrl) {
    const image = document.createElement("img");
    image.src = film.posterUrl;
    image.alt = `${film.title} poster`;
    image.loading = "lazy";
    poster.append(image);
  } else {
    poster.textContent = "No poster";
  }

  const title = document.createElement("div");
  title.className = "film-title";
  title.textContent = film.title;

  const year = document.createElement("div");
  year.className = "film-year";
  year.textContent = film.year || "Year unknown";

  const url = document.createElement("div");
  url.className = "film-url";
  url.textContent = film.url || "";

  container.append(poster, title, year, url);
}

function filmLabel(film) {
  return film.year ? `${film.title} (${film.year})` : film.title;
}

function sample(items, size) {
  return shuffle([...items]).slice(0, size);
}

function drawOne(items) {
  const index = Math.floor(Math.random() * items.length);
  const [item] = items.splice(index, 1);
  return item;
}

function shuffle(items) {
  for (let index = items.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [items[index], items[swapIndex]] = [items[swapIndex], items[index]];
  }
  return items;
}

function showNotice(message) {
  elements.notice.textContent = message;
  elements.notice.classList.remove("hidden");
}

function clearNotice() {
  elements.notice.textContent = "";
  elements.notice.classList.add("hidden");
}
