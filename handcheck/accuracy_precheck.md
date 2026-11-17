# Hand-check accuracy (20 labels, marks from premarks/ (AI pre-check of the output before fixes, in premarks_base/))

| Part | Measure | Result |
|---|---|---|
| A | Row fields parsed right | 193/280 = 68.9% (missed rows count as wrong: 47) |
| A | Identified rows with the right id | 80/86 = 93.0% |
| A | Review rows where review was right | 114/147 = 77.6% |
| B | Claims precision (reported claims that are right) | 112/114 = 98.2% |
| B | Claims recall (right claims of all claims on the label) | 112/120 = 93.3% |
| B | Candidates that are claim-like and not on the list | 39/41 = 95.1% |
| C | Evidence items right (url, status, summary) | 79/86 = 91.9% |

## Every item marked wrong

- dsld:176258 r12 parse: Palm kernel oil is not palm oil (parent 'palm oil' + source 'kernel' is wrong), and GSRS has its own UNII PALM KERNEL OIL B0S90M0233, so form_no_id is false and 5QUO05548Z (palm fruit oil) is a different oil.
- dsld:176258 r12 identity: Palm kernel oil is not palm oil (parent 'palm oil' + source 'kernel' is wrong), and GSRS has its own UNII PALM KERNEL OIL B0S90M0233, so form_no_id is false and 5QUO05548Z (palm fruit oil) is a different oil.
- dsld:206169 r1 identity: Vitamin D3 is one compound (the row itself says Alt. Name: Cholecalciferol; DSLD gives form Cholecalciferol), so CID 5280795 is exact and the row should be identified, not review form_not_given.
- dsld:206169 r5 parse: 'Nutrition Facts Per Serving' is a panel heading, not a blend: it should not be a blend_header with scope blend/listed, and the reason 'named mixture; the member rows carry the ids' is false.
- dsld:206169 r5 identity: 'Nutrition Facts Per Serving' is a panel heading, not a blend: it should not be a blend_header with scope blend/listed, and the reason 'named mixture; the member rows carry the ids' is false.
- dsld:206169 r6 parse: Nutrition line is not a blend member (role ingredient, group null, scope ingredient as in dsld:176258), and the amount 4 kcal on the label is lost (value/unit null).
- dsld:206169 r7 parse: Nutrition line is not a blend member: role should be ingredient, group null, scope ingredient.
- dsld:206169 r8 parse: Nutrition line is not a blend member: role should be ingredient, group null, scope ingredient.
- dsld:206169 r9 parse: Nutrition line is not a blend member: role should be ingredient, group null, scope ingredient.
- dsld:206169 r10 parse: Nutrition line is not a blend member: role should be ingredient, group null, scope ingredient.
- dsld:206169 r11 parse: Nutrition line is not a blend member: role should be ingredient, group null, scope ingredient.
- dsld:206169 r12 parse: Nutrition line is not a blend member: role should be ingredient, group null, scope ingredient.
- dsld:206169 r13 parse: Nutrition line is not a blend member: role should be ingredient, group null, scope ingredient.
- dsld:206169 r14 parse: Nutrition line is not a blend member: role should be ingredient, group null, scope ingredient; nearest UNII 9NEZ333N27 is Sodium.
- dsld:206169 r19 identity: CID 162651 is 'Titanium oxide (Ti3O)' (CAS 12035-95-9); titanium dioxide is CID 26042 (CAS 13463-67-7), which is what PubChem returns for the name.
- dsld:206169 r28 parse: 'Color' is the function; the row names titanium dioxide, so parent should be titanium dioxide and the row identified (CID 26042), not review not_one_substance.
- dsld:206169 r28 identity: 'Color' is the function; the row names titanium dioxide, so parent should be titanium dioxide and the row identified (CID 26042), not review not_one_substance.
- dsld:206169 r29 parse: 'Anti-caking agent' is the function; the row names beeswax, so parent should be beeswax and the row identified (UNII 2ZA36H0S2V as in r20), not review not_one_substance.
- dsld:206169 r29 identity: 'Anti-caking agent' is the function; the row names beeswax, so parent should be beeswax and the row identified (UNII 2ZA36H0S2V as in r20), not review not_one_substance.
- dsld:206169 r30 parse: 'Emulsifier' is the function; the row names sunflower lecithin, so parent should be sunflower lecithin and the row identified (UNII 834K0WOS5G as in r21), not review not_one_substance.
- dsld:206169 r30 identity: 'Emulsifier' is the function; the row names sunflower lecithin, so parent should be sunflower lecithin and the row identified (UNII 834K0WOS5G as in r21), not review not_one_substance.
- dsld:206169 missed C18: The statement 'Non-GMO, Sugar free, naturally gluten free, no artificial flavors.' gives C18; the output lacks it.
- dsld:206169 evidence r4: Hazard codes match the copy, but the added sentence 'does not name the form on this label' is false: the copy's entries are all zinc oxide, the form on the label.
- dsld:206169 evidence r19: Fetched for the wrong CID 162651 (Ti3O), so no_record; titanium dioxide CID 26042 has a PubChem GHS record (H351, H372, H319, H335, H320).
- dsld:206169 evidence r31: Hazard codes match the copy, but the added sentence 'does not name the form on this label' is false: the copy's entries are all zinc oxide, the form on the label.
- dsld:206169 evidence r32: Hazard codes match the copy, but the added sentence 'does not name the form on this label' is false: every entry in the copy is colecalciferol/cholecalciferol, the form on the label.
- dsld:212804 r2 parse: Folate (Folic Acid) is one nutrient declared as folic acid (DSLD form 'Folic Acid'), not a named mixture: parent should be folate, form folic acid, and the certain id is folic acid CID 135398658, so the 'blend_header: named mixture' reason is false.
- dsld:212804 r2 identity: Folate (Folic Acid) is one nutrient declared as folic acid (DSLD form 'Folic Acid'), not a named mixture: parent should be folate, form folic acid, and the certain id is folic acid CID 135398658, so the 'blend_header: named mixture' reason is false.
- dsld:212804 r3 identity: Folic acid is itself a specific compound and CID 135398658 is exactly Folic Acid, so the row should be identified; 'form_not_given' is a false reason.
- dsld:212804 missed C36: Allergen statement says 'Contains milk' (and Lactose (Milk) is an ingredient); C36 is missing.
- dsld:213195 r9 parse: The label gives '< 1 Gram(s)'; amount value and unit are both null, so at least the unit (Gram(s)) is lost.
- dsld:213195 r18.1 parse: CID 13506 'Amaranth' is the azo dye (trisodium naphthylazo sulphonate, FD&C Red 2), not the amaranth grain seed in the sprouted seed complex; source should be 'seed' and the row should be review (species not given; e.g. GSRS AMARANTHUS CRUENTUS SEED 0C5WAA83X5 is one candidate).
- dsld:213195 r18.1 identity: CID 13506 'Amaranth' is the azo dye (trisodium naphthylazo sulphonate, FD&C Red 2), not the amaranth grain seed in the sprouted seed complex; source should be 'seed' and the row should be review (species not given; e.g. GSRS AMARANTHUS CRUENTUS SEED 0C5WAA83X5 is one candidate).
- dsld:213195 r18.2 parse: Parent should be 'chia' with source 'seed' (black is a variety); GSRS has CHIA SEED / SALVIA HISPANICA SEED NU0OLX06F8, so no_match is only an artefact of the unnormalised name.
- dsld:213195 r18.2 identity: Parent should be 'chia' with source 'seed' (black is a variety); GSRS has CHIA SEED / SALVIA HISPANICA SEED NU0OLX06F8, so no_match is only an artefact of the unnormalised name.
- dsld:213195 r18.3 identity: UOI4FT57BZ is BROCCOLI HEAD (Brassica oleracea var. italica head), but this broccoli is in a sprouted seed complex; GSRS has 'Broccoli seed' TRV7Y4GE8Q, so identified with the head id is wrong (source 'seed' also missing).
- dsld:213195 r18.4 parse: Parent should be 'flax' with source 'seed' (golden is a variety); GSRS has FLAX SEED 4110YT348C, so no_match comes from the unnormalised name.
- dsld:213195 r18.4 identity: Parent should be 'flax' with source 'seed' (golden is a variety); GSRS has FLAX SEED 4110YT348C, so no_match comes from the unnormalised name.
- dsld:213195 r18.5 parse: Source 'seed' from 'Sprouted seed Complex' is missing.
- dsld:213195 r21 parse: Parent should be barley (Hordeum vulgare) with source grass/leaf and form juice concentrate, not the whole string 'barley grass juice conc'.
- dsld:213195 r24.2 identity: Review is right, but the reason detail 'GSRS has no such name' is false: GSRS STEVIA REBAUDIANA LEAF 6TC6NN0876 carries the name 'STEVIA [MI]' (the natural nearest id).
- dsld:21346 r1.3 identity: Label and DSLD give only the genus ('Polygonatum (unspecified)'), so W93B56AH6R (Polygonatum cyrtonema root) is one guessed species; the reason should be ambiguous_name (species not given), not form_no_id.
- dsld:21346 r1.5 identity: Reason is false: GSRS has a SCHIZANDRA concept that points to SCHISANDRA CHINENSIS FRUIT ABS794681C (the program itself uses ABS794681C for 'schizandra' in retailer:16751).
- dsld:239579 r12 parse: 'EPA/DHA' names two substances and should be split into r12.1 EPA and r12.2 DHA; source should be 'fish' (oil concentrate is the form), not 'purified fish oil concentrate'.
- dsld:239579 r15 identity: Sugar is an other ingredient, not a nutrition-facts line, so the nutrition_panel reason is false; PubChem name 'sugar' gives sucrose CID 5988.
- dsld:239579 r18.2 identity: CID 22230 is citric acid monohydrate; the label says Citric Acid, which is CID 311 (PubChem name lookup returns 311).
- dsld:239579 missed C17: States no synthetic (artificial) dyes, which is C17.
- dsld:239579 evidence r18.2: Copy and summary match CID 22230, but that is citric acid monohydrate, not the label's citric acid (CID 311), so the hazards are for the wrong substance.
- dsld:240278 r5 identity: CID 22230 is citric acid monohydrate; the label says Citric Acid, which is CID 311.
- dsld:240278 evidence r5: Copy and summary match CID 22230, but that is citric acid monohydrate, not the label's citric acid (CID 311).
- dsld:241928 r7 identity: Identity: Cholesterol is one substance with a certain id (PubChem CID 5997); the reason 'nutrition facts line, not one substance' is false.
- dsld:241928 r10 parse: Parse: Parent is mis-split as 'oil concentrate' with form 'oil'; it should be parent 'fish oil', form 'concentrate', source 'fish'. Identity: Reason 'no GSRS name oil concentrate' comes from the bad parse; GSRS has FISH OIL (UNII XGF7L72M0F), so the right call is form_no_id (concentrate) with that nearest id.
- dsld:241928 r10 identity: Parse: Parent is mis-split as 'oil concentrate' with form 'oil'; it should be parent 'fish oil', form 'concentrate', source 'fish'. Identity: Reason 'no GSRS name oil concentrate' comes from the bad parse; GSRS has FISH OIL (UNII XGF7L72M0F), so the right call is form_no_id (concentrate) with that nearest id.
- dsld:241928 r15 parse: Parse: Parent is 'oil' with form 'oil'; it should be parent 'fish oil' (source fish, form null). Identity: GSRS has the exact name FISH OIL (UNII XGF7L72M0F); the reason "no GSRS name 'oil'" is an artifact of the bad parse.
- dsld:241928 r15 identity: Parse: Parent is 'oil' with form 'oil'; it should be parent 'fish oil' (source fish, form null). Identity: GSRS has the exact name FISH OIL (UNII XGF7L72M0F); the reason "no GSRS name 'oil'" is an artifact of the bad parse.
- dsld:241928 r19 identity: Identity: GSRS lists 'MIXED TOCOPHEROLS' as a name of TOCOPHEROL (UNII R0ZB2556P8), so a certain id exists and 'not_one_substance' is a false reason (gelatin, also a mixture, was identified).
- dsld:241928 candidates 2: '3rd party tested for quality & purity' is claim C26 (Third-party tested), which is on the list and already claimed, so it is not a candidate.
- dsld:276031 r5 identity: Identity: 'Chamomile' is unspecified (German vs Roman; DSLD says 'Chamomile (unspecified)'), so the reason should be ambiguous_name; also GSRS lists 'CHAMOMILLA RECUTITA (MATRICARIA) FLOWER POWDER' under FGL3685T2X, so 'no UNII for the flower powder' is false.
- dsld:276031 candidates 1: 'Manufactured in a cGMP facility' is claim C27 (Made under GMP), already on the list and claimed, so it is not a candidate.
- dsld:55911 r2 identity: Identity: Folic acid is itself a specific form (pteroylglutamic acid, CID 135398658, which the output already found); 'form_not_given' is a false reason and the row should be identified.
- dsld:55911 r4 identity: Identity: CID 5984 is the open-chain keto form (synonyms incl. DL-fructose, CAS 30237-26-4); PubChem's 'fructose' name lookup gives CID 2723872 (D-fructose, CAS 57-48-7), which also has a GHS record.
- retailer:12509 evidence r1: Hazard codes match the copy, but the added sentence 'does not name the form on this label' is false: every entry in the copy is colecalciferol/cholecalciferol, the form the label names.
- retailer:13748 r4 parse: Parent 'bioactive neocell collagen' keeps the brand and drops 'peptides': parent should be collagen (form peptides/hydrolyzed), source bovine; review is still right because GSRS has only MW-specific hydrolysed bovine collagen (e.g. 5WE8P977RQ, 3500 MW) and the label gives no MW.
- retailer:21018 r1.1 identity: GSRS KU94FIY6JB is CARICA PAPAYA FRUIT and lists 'CARICA PAPAYA FRUIT POWDER' as a name, so the row should be identified; 'no UNII for the fruit powder' is false.
- retailer:21018 r1.3 identity: Papain is the enzyme and A236A06Y32 is exactly Papain; '(fruit)' is the source, not a form, so the row should be identified and the form_no_id reason is false.
- retailer:21622 r10 parse: Parent should be 'added sugars' with amount 0 g; the output keeps 'includes 0 g added sugars' as the parent and null amount.
- retailer:21622 C09 claim: 'Contains no added ... wheat ... ingredients' is a recipe statement (claims.md C09 'Not this': not made with wheat goes to candidates), not a wheat-free claim.
- retailer:22492 missed C08: States no gluten ingredients without a gluten-free claim, which is exactly C08; the output left it only in candidates.
- retailer:26942 r1 parse: Thiamin HCl is the form, not the source; it has a certain id (thiamine hydrochloride CID 6202), so form_not_given is false (6042 is thiamine chloride).
- retailer:26942 r1 identity: Thiamin HCl is the form, not the source; it has a certain id (thiamine hydrochloride CID 6202), so form_not_given is false (6042 is thiamine chloride).
- retailer:26942 r2 identity: Riboflavin is one compound with a certain id (CID 493570, the id given), so it should be identified; form_not_given is not a real reason.
- retailer:26942 r4 parse: Pyridoxine HCl is the form, not the source; it has a certain id (pyridoxine hydrochloride CID 6019), so form_not_given is false.
- retailer:26942 r4 identity: Pyridoxine HCl is the form, not the source; it has a certain id (pyridoxine hydrochloride CID 6019), so form_not_given is false.
- retailer:26942 r7 parse: Calcium pantothenate is the form, not the source; it has a certain id (CID 443753), so form_not_given is false.
- retailer:26942 r7 identity: Calcium pantothenate is the form, not the source; it has a certain id (CID 443753), so form_not_given is false.
- retailer:26942 r8 parse: Potassium iodide is the form, not the source; it has a certain id (CID 4875), so form_not_given is false (807 is elemental I2).
- retailer:26942 r8 identity: Potassium iodide is the form, not the source; it has a certain id (CID 4875), so form_not_given is false (807 is elemental I2).
- retailer:26942 r9 parse: Magnesium malate is the form, not the source; it has a certain id (CID 164748), so form_not_given is false.
- retailer:26942 r9 identity: Magnesium malate is the form, not the source; it has a certain id (CID 164748), so form_not_given is false.
- retailer:26942 r10 parse: Chromium nicotinate glycinate is the form, not the source; review is right but the reason should be form_no_id (no PubChem name), not form_not_given.
- retailer:26942 r10 identity: Chromium nicotinate glycinate is the form, not the source; review is right but the reason should be form_no_id (no PubChem name), not form_not_given.
- retailer:26942 r12 parse: The row also names maltodextrin ([Guarana Extract (Seed), Maltodextrin]), which is dropped; it should be split or shown as a mixture. C21GE7524R carries the GSRS name GUARANA EXTRACT.
- retailer:26942 r14 parse: The row also names maltodextrin ([Yerba Mate Extract (Leaf), Maltodextrin]), which is dropped. 1Q953B4O4F carries the GSRS name YERBA MATE EXTRACT.
- retailer:26942 r15 identity: Not ambiguous: Sedum roseum is a synonym of Rhodiola rosea and 3S5ITS5ULN carries the GSRS name RHODIOLA ROSEA ROOT EXTRACT (NCBI Rhodiola rosea is 203015, not genus 202994); it should be identified as 3S5ITS5ULN.
- retailer:26942 r19 parse: Parent has a stray bracket ('l-carnitine )'); it should be 'l-carnitine'. CID 10917 (-)-carnitine is right.
- retailer:26942 missed C28: Says the product is made in the USA.
- retailer:26942 missed C08: Says no gluten ingredients without saying gluten free (C08); the rest of the sentence can stay a candidate.
- retailer:30326 missed C24: States that NSF certifies the product (for non-GMO); arguably C24 and at least a candidate.
- retailer:62350 r1.1 parse: Parse: Verbatim and parent dropped the genus and the strain: it should be 'Lactobacillus rhamnosus (GR-1)', parent 'lactobacillus rhamnosus', strain 'GR-1'. Identity: Reason "no name 'rhamnosus'" comes from the bad split; it should be strain_no_id (NCBI has no GR-1 taxon) with nearest species id 47715 Lacticaseibacillus rhamnosus.
- retailer:62350 r1.1 identity: Parse: Verbatim and parent dropped the genus and the strain: it should be 'Lactobacillus rhamnosus (GR-1)', parent 'lactobacillus rhamnosus', strain 'GR-1'. Identity: Reason "no name 'rhamnosus'" comes from the bad split; it should be strain_no_id (NCBI has no GR-1 taxon) with nearest species id 47715 Lacticaseibacillus rhamnosus.
- retailer:62350 r2 parse: Parse: Parent should be 'inulin' (the named substance, form powder); 'prebiotic fiber' is a descriptor. Identity: GSRS has Inulin (UNII JOS53KRJ01), so 'not_one_substance' is false; at most form_no_id for the powder with that id.
- retailer:62350 r2 identity: Parse: Parent should be 'inulin' (the named substance, form powder); 'prebiotic fiber' is a descriptor. Identity: GSRS has Inulin (UNII JOS53KRJ01), so 'not_one_substance' is false; at most form_no_id for the powder with that id.
- retailer:62350 C07 claim: 'Made Without: ... gluten' is a recipe/ingredient statement (claims.md treats 'not made with wheat' as recipe text), so it is C08 No gluten ingredients, not C07 Gluten free.
- retailer:62350 missed C08: The gluten part of the 'Made Without' line is C08 (no gluten ingredients), not C07.
- retailer:64033 r6 parse: Parse: blend_contents should be 'listed': the label lists LGG and BB-12 under the Proprietary Probiotic Blend (rows r7, r8).
- retailer:64033 r7 parse: Parse: Row is a member of the blend r6: role should be blend_member, group 'r6', amount scope 'member'. Identity: NCBI has the strain taxon Lacticaseibacillus rhamnosus GG (taxid 568703), so 'strain_no_id: no NCBI taxonomy id for strain LGG' is false; the row should be identified with 568703.
- retailer:64033 r7 identity: Parse: Row is a member of the blend r6: role should be blend_member, group 'r6', amount scope 'member'. Identity: NCBI has the strain taxon Lacticaseibacillus rhamnosus GG (taxid 568703), so 'strain_no_id: no NCBI taxonomy id for strain LGG' is false; the row should be identified with 568703.
- retailer:64033 r8 parse: Parse: Row is a member of the blend r6: role should be blend_member, group 'r6', amount scope 'member'.
