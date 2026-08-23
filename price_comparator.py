from backend.comparison import search_products, find_cheapest


# Ask the user what they want
search = input("\nWhat grocery product do you want to compare? ")


# Search the database
results = search_products(search)


# Check if we found anything
if not results:

    print("\n❌ Product not found.")
    print("Try another search.")

    exit()


# Find cheapest
cheapest = find_cheapest(results)


# Display results
print("\n==============================")
print("   GROCERY PRICE COMPARISON")
print("==============================\n")

print("Search:", search)
print()


for result in results:

    product_name = result[0]
    brand = result[1]
    quantity = result[2]
    unit = result[3]
    retailer = result[4]
    price = result[5]

    print(
        f"{retailer:<12} ₹{price}"
    )


print("\n------------------------------")

print(
    f"🏆 Cheapest: {cheapest[4]}"
)

print(
    f"💰 Price: ₹{cheapest[5]}"
)

print("------------------------------")