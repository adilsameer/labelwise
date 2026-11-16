# Claims list (40 claims)

- A claim is a statement on the label about the whole product. An ingredient name, a serving size or an address is not a claim, unless the definition says so.
- A risk statement ("may contain milk", "made in a facility that also processes soy") is not a Contains claim. Put it in `candidates`.
- A claim with an exception ("gluten free except the capsule") is not the claim. Put it in `for_a_person` with kind `exception`.
- If a claim conflicts with the label (for example "Vegan" and gelatin in the ingredients), keep the claim and add a `conflict` to `for_a_person`.
- Claim-like text that is not on this list goes in `candidates`.

| ID | Claim | Group | Definition | Not this |
|---|---|---|---|---|
| C01 | Vegan | Diet | The label states that the product is vegan or suitable for vegans. | "Vegan capsule" when it names only the capsule. |
| C02 | Vegetarian | Diet | The label states that the product is vegetarian or suitable for vegetarians. | "1 Vegetarian Capsule" as the serving size or the count. |
| C03 | Kosher | Diet | The label states that the product is kosher or kosher certified, for example "Kosher Parve". | |
| C04 | Halal | Diet | The label states that the product is halal or halal certified. | |
| C05 | Keto | Diet | The label states that the product is keto or keto friendly. | "Ketones" in an ingredient name. |
| C06 | Paleo | Diet | The label states that the product is paleo or paleo friendly. | |
| C07 | Gluten free | Free from: allergens | The label states that the finished product is gluten free or contains no gluten. | "No gluten ingredients" (that is C08). |
| C08 | No gluten ingredients | Free from: allergens | The label states that no ingredient contains gluten, but does not state that the product is gluten free. | "Gluten free" (that is C07). |
| C09 | Wheat free | Free from: allergens | The label states that the finished product is wheat free or contains no wheat. | "Not made with wheat" (a recipe statement; put it in candidates). |
| C10 | Dairy free | Free from: allergens | The label states that the product contains no dairy or no milk. | "Lactose free" (put it in candidates). |
| C11 | Soy free | Free from: allergens | The label states that the product contains no soy. | "Non-GMO soy" (the product contains soy). |
| C12 | Nut free | Free from: allergens | The label states that the product contains no tree nuts and no peanuts. | "Peanut free" or "tree nut free" alone (put it in candidates). |
| C13 | Egg free | Free from: allergens | The label states that the product contains no egg. | |
| C14 | Shellfish free | Free from: allergens | The label states that the product contains no shellfish or no crustaceans. | "Fish free" (put it in candidates). |
| C15 | Sugar free | Sugar | The label states that the product has no sugar, for example "sugar free" or "zero sugar". | "No added sugar" (that is C16); "0 g" in a Total Sugars row. |
| C16 | No added sugar | Sugar | The label states that no sugar is added to the product. | "Sugar free" (that is C15). |
| C17 | No artificial colors | Free from: additives | The label states that the product has no artificial colors or dyes. | "Natural color" in the ingredient list. |
| C18 | No artificial flavors | Free from: additives | The label states that the product has no artificial flavors. | "Natural flavors" in the ingredient list. |
| C19 | No artificial preservatives | Free from: additives | The label states that the product has no preservatives or no artificial preservatives. | |
| C20 | Non-GMO | Free from: additives | The label states that the product or its ingredients are non-GMO or GMO free, including "Non-GMO Project Verified". | |
| C21 | No stearates | Free from: additives | The label states that the product has no magnesium stearate or no stearates. | |
| C22 | Organic product | Certification and quality | The label states that the whole product is organic, for example "USDA Organic", "Certified Organic" or a product name that starts with "Organic". | "Made with organic ingredients" (that is C23); one ingredient row named "organic ...". |
| C23 | Made with organic ingredients | Certification and quality | The label states that the product is made with organic ingredients, but does not state that the whole product is organic. | "USDA Organic" (that is C22). |
| C24 | NSF certified | Certification and quality | The label states that NSF certifies the product, for example "NSF Certified for Sport". | "Made in an NSF-registered GMP facility" (that is C27). |
| C25 | Informed Sport certified | Certification and quality | The label states that Informed Sport or Informed Choice certifies the product. | |
| C26 | Third-party tested | Certification and quality | The label states that an independent (third-party) laboratory tests the product. | "Tested for purity" with no independent party. |
| C27 | Made under GMP | Certification and quality | The label states that the product is made under Good Manufacturing Practice (GMP or cGMP), which is a manufacturing statement and not a certification. | A GMP or cGMP statement alone does not give C24 or C26. |
| C28 | Made in USA | Origin | The label states that the product is made, manufactured or produced in the USA. | A US address after "Distributed by" or "Manufactured for". |
| C29 | Whole food | Form and process | The label states that the product or its nutrients come from whole foods. | |
| C30 | Fermented | Form and process | The label states that the product or its ingredients are fermented. | A list of probiotic strains with no statement about fermentation. |
| C31 | Enteric coated | Form and process | The label states that the tablet or capsule is enteric coated or delayed release, so that it opens after the stomach. | |
| C32 | Chewable | Form and process | The label states that the product is chewable or that you chew it. | "Swallow whole. Do not chew." |
| C33 | For children | Audience | The label states that the product is made for children, for example "for kids" or "children's". | "Keep out of reach of children." |
| C34 | For women | Audience | The label states that the product is made for women. | "Pregnant or nursing women: ask a doctor before use." |
| C35 | Prenatal | Audience | The label states that the product is for use before or during pregnancy. | "If pregnant or nursing, ask your doctor." |
| C36 | Contains milk | Contains | The label states in a "Contains" or allergen statement that the product contains milk. | "May contain milk"; "made in a facility that also processes milk" (put it in candidates). |
| C37 | Contains soy | Contains | The label states in a "Contains" or allergen statement that the product contains soy. | "May contain soy" (put it in candidates). |
| C38 | Contains fish | Contains | The label states in a "Contains" or allergen statement that the product contains fish. | "Fish oil" in an ingredient row with no allergen statement. |
| C39 | Contains tree nuts | Contains | The label states in a "Contains" or allergen statement that the product contains tree nuts, for example almond or cashew. | |
| C40 | Contains gelatin | Contains | The label states that the product contains gelatin, or names gelatin as an ingredient or as the capsule material. | "Gelatin free". |
