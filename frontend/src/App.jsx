import { useState } from "react";
import "./App.css";

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

  async function comparePrices() {
    if (!search.trim()) {
      setResult({
        success: false,
        message: "Enter a product name to start comparing.",
      });
      return;
    }

    if (!location.trim()) {
      setResult({
        success: false,
        message: "Enter your PIN code to check local availability.",
      });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const url =
        `https://grocery-price-bot-umiu.onrender.com/compare` +
        `?search=${encodeURIComponent(search)}` +
        `&location=${encodeURIComponent(location)}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error("Backend request failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error(error);

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
          </div>

        </div>
      </nav>


      {/* HERO */}

      <main>

        <section className="hero">

          <div className="hero-glow glow-one"></div>
          <div className="hero-glow glow-two"></div>

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


            {/* SEARCH PANEL */}

            <div className="search-panel">

              <div className="search-field">

                <div className="field-icon">
                  ⌕
                </div>

                <div className="field-content">

                  <label>
                    WHAT ARE YOU LOOKING FOR?
                  </label>

                  <input
                    value={search}
                    onChange={(event) =>
                      setSearch(event.target.value)
                    }
                    onKeyDown={handleKeyDown}
                    placeholder="Try “Amul Taaza Milk 1L”"
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
                    value={location}
                    onChange={(event) =>
                      setLocation(
                        event.target.value.replace(/\D/g, "")
                      )
                    }
                    onKeyDown={handleKeyDown}
                    placeholder="PIN code"
                    maxLength={6}
                  />

                </div>

              </div>


              <button
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
                    <span className="button-arrow">→</span>
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

          {loading && (
            <LoadingState />
          )}


          {result && !result.success && (
            <div className="message-card error-card">
              <div className="message-icon">!</div>

              <div>
                <strong>Something needs your attention</strong>
                <p>{result.message}</p>
              </div>
            </div>
          )}


          {result &&
            result.success &&
            result.available_anywhere === false && (
              <UnavailableResult result={result} />
            )}


          {result &&
            result.success &&
            result.available_anywhere === true && (
              <ComparisonResult result={result} />
            )}


          {!result && !loading && (
            <EmptyState />
          )}

        </section>

      </main>


      {/* FOOTER */}

      <footer className="footer">

        <div>
          GroceryCompare
        </div>

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

      <h3>
        Comparing prices
      </h3>

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

  const available = result.prices.filter(
    (item) => item.available
  );

  const unavailable = result.prices.filter(
    (item) => !item.available
  );

  return (
    <div className="comparison-container">

      {/* RESULT HEADER */}

      <div className="result-heading">

        <div>

          <div className="result-eyebrow">
            PRICE COMPARISON
          </div>

          <h2>
            {result.product.name}
          </h2>

          <p>
            {result.product.brand}
            {" · "}
            {result.product.quantity}
            {result.product.unit}
            {" · "}
            <span className="location-text">
              PIN {result.location}
            </span>
          </p>

        </div>

        <div className="checked-badge">
          <span>●</span>
          Live check
        </div>

      </div>


      {/* WINNER */}

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
            ₹{cheapest.price}
          </div>

          {result.maximum_saving > 0 && (
            <div className="saving-pill">
              Save ₹{result.maximum_saving}
            </div>
          )}

        </div>

      </div>


      {/* AVAILABLE */}

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
              item.platform === cheapest.platform
            }
          />
        ))}

      </div>


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


      {/* DISCLAIMER */}

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

function PlatformCard({
  item,
  winner
}) {

  const meta =
    PLATFORM_META[item.platform] || {
      icon: "•",
      className: "default"
    };

  return (
    <div
      className={
        winner
          ? "platform-card winner-platform-card"
          : item.available
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
              item.available
                ? "status available-status"
                : "status unavailable-status"
            }
          >
            <span className="status-dot"></span>

            {item.available
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

          {item.available
            ? `₹${item.price}`
            : `₹${item.price}`}

        </div>

        <div className="platform-location">
          📍 {item.location}
        </div>

      </div>

    </div>
  );
}


/* ============================================================
   UNAVAILABLE RESULT
   ============================================================ */

function UnavailableResult({ result }) {

  return (
    <div className="comparison-container">

      <div className="result-heading">

        <div>

          <div className="result-eyebrow">
            PRICE COMPARISON
          </div>

          <h2>
            {result.product?.name}
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
          unavailable on the checked platforms for this location.
        </p>

      </div>


      <div className="platform-grid">

        {result.prices.map((item) => (
          <PlatformCard
            key={item.platform}
            item={item}
          />
        ))}

      </div>

    </div>
  );
}


export default App;