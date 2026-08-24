import { useState } from "react";
import "./App.css";

const API_URL = "https://grocery-price-bot-backend-vivek.onrender.com";

const PLATFORM_META = {
  Blinkit: { icon: "⚡", className: "blinkit" },
  Zepto: { icon: "Z", className: "zepto" },
  Instamart: { icon: "S", className: "instamart" },
  BigBasket: { icon: "B", className: "bigbasket" },
  "Amazon Fresh": { icon: "A", className: "amazon" },
  "Flipkart Minutes": { icon: "F", className: "flipkart" },
  JioMart: { icon: "J", className: "jiomart" },
  "DMart Ready": { icon: "D", className: "dmart" },
};

function App() {
  const [search, setSearch] = useState("");
  const [location, setLocation] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleSearchChange(event) {
    const value = event.target.value;

    // Allow only letters, numbers and spaces.
    const cleaned = value.replace(/[^a-zA-Z0-9 ]/g, "");

    setSearch(cleaned);
  }

  function handleLocationChange(event) {
    const value = event.target.value;

    // PIN code: numbers only, maximum 6 digits.
    const cleaned = value.replace(/\D/g, "").slice(0, 6);

    setLocation(cleaned);
  }

  async function comparePrices() {
    const product = search.trim();
    const pin = location.trim();

    if (!product) {
      setResult({
        success: false,
        message: "Enter a product name to start comparing.",
      });
      return;
    }

    if (!/^[a-zA-Z0-9 ]+$/.test(product)) {
      setResult({
        success: false,
        message: "Product name can contain only letters, numbers and spaces.",
      });
      return;
    }

    if (!/^\d{6}$/.test(pin)) {
      setResult({
        success: false,
        message: "Enter a valid 6-digit PIN code.",
      });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const url =
        `${API_URL}/compare` +
        `?search=${encodeURIComponent(product)}` +
        `&location=${encodeURIComponent(pin)}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Backend request failed: ${response.status}`);
      }

      const data = await response.json();

      /*
       * NORMALIZE PROVIDER DATA
       *
       * A provider is available when:
       *
       *   available === true
       *
       * OR
       *
       *   status === "LIVE"
       *
       * This is important because BigBasket returns LIVE provider
       * data and the UI must consistently treat it as available.
       */
      if (Array.isArray(data.prices)) {
        data.prices = data.prices.map((item) => {
          const isLive =
            item.available === true ||
            String(item.status || "").toUpperCase() === "LIVE";

          return {
            ...item,
            available: isLive,

            /*
             * Normalize price so the UI always receives a number.
             * Null/undefined/empty values remain null.
             */
            price:
              item.price !== null &&
              item.price !== undefined &&
              item.price !== ""
                ? Number(item.price)
                : null,
          };
        });
      }

      /*
       * Keep providers synchronized too, if the backend includes them.
       */
      if (Array.isArray(data.providers)) {
        data.providers = data.providers.map((item) => ({
          ...item,
          available:
            item.available === true ||
            String(item.status || "").toUpperCase() === "LIVE",

          price:
            item.price !== null &&
            item.price !== undefined &&
            item.price !== ""
              ? Number(item.price)
              : null,
        }));
      }

      /*
       * Recalculate available_anywhere from the normalized prices.
       */
      if (Array.isArray(data.prices)) {
        data.available_anywhere = data.prices.some(
          (item) => item.available === true
        );
      }

      /*
       * Also normalize cheapest when present.
       *
       * This prevents the winner card from disagreeing with
       * the provider cards.
       */
      if (data.cheapest) {
        data.cheapest = {
          ...data.cheapest,

          available:
            data.cheapest.available === true ||
            String(data.cheapest.status || "").toUpperCase() === "LIVE",

          price:
            data.cheapest.price !== null &&
            data.cheapest.price !== undefined &&
            data.cheapest.price !== ""
              ? Number(data.cheapest.price)
              : null,
        };
      }

      setResult(data);
    } catch (error) {
      console.error("Comparison error:", error);

      setResult({
        success: false,
        message:
          "We couldn't connect to the comparison service. Make sure the backend is running.",
      });
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter") {
      comparePrices();
    }
  }

  return (
    <div className="app">
      {/* NAVBAR */}

      <nav className="navbar">
        <div className="nav-inner">
          <div className="brand">
            <div className="brand-mark">G</div>

            <div>
              <div className="brand-name">
                Grocery<span>Compare</span>
              </div>

              <div className="brand-caption">
                Find it cheaper
              </div>
            </div>
          </div>

          <div className="nav-right">
            <span className="privacy-badge">
              <span className="privacy-dot"></span>
              No account required
            </span>

            <a
              href="https://www.linkedin.com/in/sinha027/"
              target="_blank"
              rel="noopener noreferrer"
              className="vivek-watermark"
              aria-label="Built by Vivek Sinha on LinkedIn"
            >
              <span className="creator-name">
                Built by Vivek Sinha
              </span>

              <span className="creator-link">
                · LinkedIn ↗
              </span>
            </a>
          </div>
        </div>
      </nav>

      {/* HERO */}

      <main>
        <section className="hero">
          <div className="hero-content">
            <div className="eyebrow">
              <span className="eyebrow-dot"></span>
              Smart grocery price comparison
            </div>

            <h1>
              Shop smarter.
              <br />
              <span>Pay less.</span>
            </h1>

            <p className="hero-description">
              Compare product prices and availability across
              grocery and quick-commerce platforms in one place.
            </p>

            {/* SEARCH */}

            <div className="search-panel">
              <div className="search-field">
                <div className="field-icon">⌕</div>

                <div className="field-content">
                  <label>
                    WHAT ARE YOU LOOKING FOR?
                  </label>

                  <input
                    type="text"
                    value={search}
                    onChange={handleSearchChange}
                    onKeyDown={handleKeyDown}
                    placeholder="Try “Amul Taaza Milk 1L”"
                    autoComplete="off"
                    inputMode="text"
                  />
                </div>
              </div>

              <div className="search-divider"></div>

              <div className="location-field">
                <div className="field-icon location-icon">
                  ⌖
                </div>

                <div className="field-content">
                  <label>
                    YOUR LOCATION
                  </label>

                  <input
                    type="text"
                    value={location}
                    onChange={handleLocationChange}
                    onKeyDown={handleKeyDown}
                    placeholder="Enter 6-digit PIN"
                    maxLength={6}
                    inputMode="numeric"
                    pattern="[0-9]*"
                    autoComplete="postal-code"
                  />
                </div>
              </div>

              <button
                type="button"
                className="compare-button"
                onClick={comparePrices}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Comparing
                  </>
                ) : (
                  <>
                    Compare prices
                    <span className="button-arrow">
                      →
                    </span>
                  </>
                )}
              </button>
            </div>

            <div className="search-note">
              <span>✦</span>
              No signup. No phone number. No payment details.
            </div>
          </div>
        </section>

        {/* RESULTS */}

        <section className="results-section">
          {loading && <LoadingState />}

          {result && !result.success && (
            <div className="message-card error-card">
              <div className="message-icon">!</div>

              <div>
                <strong>
                  Something needs your attention
                </strong>

                <p>{result.message}</p>
              </div>
            </div>
          )}

          {result &&
            result.success &&
            Array.isArray(result.prices) &&
            result.prices.some(
              (item) => item.available === true
            ) && (
              <ComparisonResult result={result} />
            )}

          {result &&
            result.success &&
            Array.isArray(result.prices) &&
            !result.prices.some(
              (item) => item.available === true
            ) && (
              <UnavailableResult result={result} />
            )}

          {!result && !loading && <EmptyState />}
        </section>
      </main>

      {/* FOOTER */}

      <footer className="footer">
        <div>GroceryCompare</div>

        <span>
          Compare smarter. Shop better.
        </span>
      </footer>
    </div>
  );
}

/* ============================================================
   LOADING
   ============================================================ */

function LoadingState() {
  return (
    <div className="loading-card">
      <div className="loading-orbit">
        <div></div>
      </div>

      <h3>Comparing prices</h3>

      <p>
        Checking available platforms for your location...
      </p>
    </div>
  );
}

/* ============================================================
   EMPTY STATE
   ============================================================ */

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        ✦
      </div>

      <h3>
        Your best deal is one search away
      </h3>

      <p>
        Search for a product and enter your PIN code.
        We'll compare the available results.
      </p>
    </div>
  );
}

/* ============================================================
   COMPARISON RESULT
   ============================================================ */

function ComparisonResult({ result }) {
  const cheapest = result.cheapest;

  /*
   * SINGLE AVAILABILITY RULE
   *
   * This is intentionally the same rule used during
   * API normalization and inside PlatformCard.
   */
  const isItemAvailable = (item) =>
    item.available === true ||
    String(item.status || "").toUpperCase() === "LIVE";

  /*
   * AVAILABLE PLATFORMS
   */
  const available = Array.isArray(result.prices)
    ? result.prices.filter(isItemAvailable)
    : [];

  /*
   * UNAVAILABLE PLATFORMS
   */
  const unavailable = Array.isArray(result.prices)
    ? result.prices.filter(
        (item) => !isItemAvailable(item)
      )
    : [];

  return (
    <div className="comparison-container">
      <div className="result-heading">
        <div>
          <div className="result-eyebrow">
            PRICE COMPARISON
          </div>

          <h2>
            {result.product?.name || result.search}
          </h2>

          <p>
            {result.product?.brand && (
              <>
                {result.product.brand}
                {" · "}
              </>
            )}

            {result.product?.quantity && (
              <>
                {result.product.quantity}{" "}
              </>
            )}

            {result.product?.unit && (
              <>
                {result.product.unit}
                {" · "}
              </>
            )}

            <span className="location-text">
              PIN {result.location}
            </span>
          </p>
        </div>

        <div className="checked-badge">
          <span>●</span>
          Latest check
        </div>
      </div>

      {/* WINNER */}

      {cheapest &&
        (
          cheapest.available === true ||
          String(cheapest.status || "").toUpperCase() === "LIVE"
        ) &&
        cheapest.price !== null &&
        cheapest.price !== undefined && (
          <div className="winner-card">
            <div className="winner-left">
              <div className="trophy">
                🏆
              </div>

              <div>
                <div className="winner-label">
                  CHEAPEST AVAILABLE
                </div>

                <div className="winner-platform">
                  {cheapest.platform}
                </div>

                <div className="winner-subtitle">
                  Available at your location
                </div>
              </div>
            </div>

            <div className="winner-right">
              <div className="winner-price">
                ₹{Number(cheapest.price).toFixed(2)}
              </div>

              {result.maximum_saving > 0 && (
                <div className="saving-pill">
                  Save ₹
                  {Number(
                    result.maximum_saving
                  ).toFixed(2)}
                </div>
              )}
            </div>
          </div>
        )}

      {/* AVAILABLE */}

      {available.length > 0 && (
        <>
          <div className="section-heading">
            <div>
              <span className="section-dot available-dot"></span>
              Available now
            </div>

            <span>
              {available.length} platforms
            </span>
          </div>

          <div className="platform-grid">
            {available.map((item) => (
              <PlatformCard
                key={item.platform}
                item={item}
                winner={
                  cheapest &&
                  item.platform === cheapest.platform
                }
              />
            ))}
          </div>
        </>
      )}

      {/* UNAVAILABLE */}

      {unavailable.length > 0 && (
        <>
          <div className="section-heading unavailable-heading">
            <div>
              <span className="section-dot unavailable-dot"></span>
              Currently unavailable
            </div>

            <span>
              {unavailable.length} platforms
            </span>
          </div>

          <div className="platform-grid">
            {unavailable.map((item) => (
              <PlatformCard
                key={item.platform}
                item={item}
                winner={false}
              />
            ))}
          </div>
        </>
      )}

      <div className="result-footnote">
        <span>◷</span>
        Prices and availability can change.
        Results shown are based on the latest available check.
      </div>
    </div>
  );
}

/* ============================================================
   PLATFORM CARD
   ============================================================ */

function PlatformCard({ item, winner }) {
  const meta =
    PLATFORM_META[item.platform] || {
      icon: "•",
      className: "default",
    };

  /*
   * IMPORTANT:
   * Never force availability to true.
   *
   * Use the actual normalized provider data.
   */
  const isAvailable =
    item.available === true ||
    String(item.status || "").toUpperCase() === "LIVE";

  return (
    <div
      className={
        winner
          ? "platform-card winner-platform-card"
          : isAvailable
            ? "platform-card"
            : "platform-card unavailable-card"
      }
    >
      <div className="platform-top">
        <div
          className={`platform-logo ${meta.className}`}
        >
          {meta.icon}
        </div>

        <div className="platform-info">
          <strong>
            {item.platform}
          </strong>

          <span
            className={
              isAvailable
                ? "status available-status"
                : "status unavailable-status"
            }
          >
            <span className="status-dot"></span>

            {isAvailable
              ? "Available"
              : "Out of stock"}
          </span>
        </div>

        {winner && (
          <div className="best-tag">
            BEST
          </div>
        )}
      </div>

      <div className="platform-bottom">
        <div className="platform-price">
          {item.price !== null &&
          item.price !== undefined &&
          !Number.isNaN(Number(item.price))
            ? `₹${Number(item.price).toFixed(2)}`
            : "—"}
        </div>

        <div className="platform-location">
          📍 {item.location || "Location unavailable"}
        </div>

        {item.product_url && (
          <a
            href={item.product_url}
            target="_blank"
            rel="noopener noreferrer"
            className="view-product"
          >
            View product →
          </a>
        )}
      </div>
    </div>
  );
}

/* ============================================================
   UNAVAILABLE RESULT
   ============================================================ */

function UnavailableResult({ result }) {
  const prices = Array.isArray(result.prices)
    ? result.prices
    : [];

  return (
    <div className="comparison-container">
      <div className="result-heading">
        <div>
          <div className="result-eyebrow">
            PRICE COMPARISON
          </div>

          <h2>
            {result.product?.name || result.search}
          </h2>

          <p>
            PIN {result.location}
          </p>
        </div>
      </div>

      <div className="all-unavailable">
        <div className="all-unavailable-icon">
          ×
        </div>

        <h3>
          Not available right now
        </h3>

        <p>
          This product was found, but it is currently
          unavailable on the checked platforms for this
          location.
        </p>
      </div>

      {prices.length > 0 && (
        <div className="platform-grid">
          {prices.map((item) => (
            <PlatformCard
              key={item.platform}
              item={item}
              winner={false}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default App;