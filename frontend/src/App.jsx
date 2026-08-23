import { useState } from "react";
import "./App.css";

function App() {
  const [search, setSearch] = useState("");
  const [location, setLocation] = useState("");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function comparePrices() {
    if (!search.trim()) {
      alert("Please enter a product name.");
      return;
    }

    if (!location.trim()) {
      alert("Please enter your PIN code.");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const url =
        `http://localhost:8000/compare` +
        `?search=${encodeURIComponent(search)}` +
        `&location=${encodeURIComponent(location)}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error("Backend request failed.");
      }

      const data = await response.json();

      setResult(data);
    } catch (error) {
      console.error(error);

      setResult({
        success: false,
        message: "Could not connect to the price comparison server."
      });
    }

    setLoading(false);
  }

  return (
    <div className="app">

      {/* HEADER */}

      <header className="header">

        <div className="logo">
          🛒 Grocery Price Bot
        </div>

        <p>
          Compare grocery prices and find the cheapest
          available option near you.
        </p>

      </header>


      {/* MAIN */}

      <main className="main">

        {/* SEARCH */}

        <section className="search-card">

          <label>
            What product do you want?
          </label>

          <input
            type="text"
            placeholder="Example: Amul Taaza Milk 1L"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                comparePrices();
              }
            }}
          />


          <label>
            📍 Delivery PIN code
          </label>

          <input
            type="text"
            placeholder="Example: 110001"
            value={location}
            onChange={(event) =>
              setLocation(event.target.value)
            }
            maxLength={6}
          />


          <button
            onClick={comparePrices}
            disabled={loading}
          >
            {loading
              ? "Comparing prices..."
              : "🔎 Compare Prices"}
          </button>

        </section>


        {/* LOADING */}

        {loading && (

          <div className="loading">
            Checking prices and availability...
          </div>

        )}


        {/* ERROR */}

        {result && !result.success && (

          <div className="error">

            ❌

            <div>
              {result.message}
            </div>

          </div>

        )}


        {/* PRODUCT NOT AVAILABLE ANYWHERE */}

        {result &&
          result.success &&
          result.available_anywhere === false && (

            <section className="results-card">

              <h2>
                {result.product?.name}
              </h2>

              <p>
                📍 {result.location}
              </p>

              <div className="unavailable-message">

                🔴 Product is currently unavailable
                on all platforms.

              </div>


              <PriceList
                prices={result.prices}
              />

            </section>

          )}


        {/* SUCCESS */}

        {result &&
          result.success &&
          result.available_anywhere === true && (

            <section className="results-card">

              {/* PRODUCT */}

              <div className="product-header">

                <h2>
                  {result.product.name}
                </h2>

                <p>
                  {result.product.brand}
                  {" • "}
                  {result.product.quantity}
                  {result.product.unit}
                </p>

                <p>
                  📍 {result.location}
                </p>

              </div>


              {/* WINNER */}

              <div className="winner">

                <div className="winner-label">
                  🏆 CHEAPEST AVAILABLE
                </div>

                <div className="winner-platform">
                  {result.cheapest.platform}
                </div>

                <div className="winner-price">
                  ₹{result.cheapest.price}
                </div>

              </div>


              {/* SAVING */}

              <div className="saving">

                💰 Maximum saving among
                available platforms:

                <strong>
                  ₹{result.maximum_saving}
                </strong>

              </div>


              {/* ALL PLATFORMS */}

              <h3>
                Price & Availability
              </h3>

              <PriceList
                prices={result.prices}
                cheapest={result.cheapest}
              />

            </section>

          )}

      </main>


      {/* FOOTER */}

      <footer>

        Prices are currently demonstration
        data while we build the live integrations.

      </footer>

    </div>
  );
}


/* ============================================================
   PRICE LIST COMPONENT
   ============================================================ */

function PriceList({
  prices,
  cheapest
}) {

  return (

    <div className="price-list">

      {prices.map((item) => {

        const isCheapest =
          cheapest &&
          item.platform === cheapest.platform &&
          item.available === true;

        return (

          <div
            className={
              isCheapest
                ? "price-row cheapest"
                : "price-row"
            }
            key={item.platform}
          >

            <div className="platform">

              <strong>
                {item.platform}
              </strong>

              <span
                className={
                  item.available
                    ? "available"
                    : "unavailable"
                }
              >
                {item.available
                  ? "🟢 Available"
                  : "🔴 Unavailable"}
              </span>

            </div>


            <div className="price">

              ₹{item.price}

            </div>

          </div>

        );
      })}

    </div>

  );
}


export default App;