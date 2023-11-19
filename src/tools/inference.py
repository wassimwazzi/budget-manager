import logging
from thefuzz import fuzz
from src.tools.text_classifier import SimpleClassifier, fuzzy_search

logger = logging.getLogger("main").getChild(__name__)
text_classifier = SimpleClassifier()

def infer_categories(df, categories, db):
    """
    Auto fill the category column when missing.
    If the category is already in the db, use that
    If the code is the same as a previous transaction (fuzzy search), use that category
    Otherwise, use NLP to infer category
    """

    prev_inferred_transactions = db.select(
        """
            SELECT description, code, category FROM transactions
            WHERE (code IS NOT NULL OR description IS NOT NULL)
            AND category != 'Other'
            AND inferred_category = 0
        """,
        [],
    )
    prev_non_inferred_transactions = db.select(
        """
            SELECT description, code, category FROM transactions
            WHERE (code IS NOT NULL OR description IS NOT NULL)
            AND inferred_category = 0
        """,
        [],
    )
    new_categories = []
    inferred_categories = []
    prev_inferred_codes = {row[1]: row[2] for row in prev_inferred_transactions if row[1]}
    prev_inferred_descriptions = {row[0]: row[2] for row in prev_inferred_transactions if row[0]}
    prev_non_inferred_codes = {row[1]: row[2] for row in prev_non_inferred_transactions if row[1]}
    prev_non_inferred_descriptions = {row[0]: row[2] for row in prev_non_inferred_transactions if row[0]}
    for _, row in df.iterrows():
        logger.debug("Infering category for\n %s", row)
        if row["Category"] in categories:
            logger.debug(
                "Using existing category %s for row",
                row["Category"],
            )
            new_categories.append(row["Category"])
            inferred_categories.append(False)
            continue
        code = row["Code"]
        description = row["Description"]
        if not code and not description:
            logger.debug(
                "Using default category Other as no description or code. %s", row
            )
            new_categories.append("Other")
            inferred_categories.append(True)
            continue

        if code:
            # Prioritise non-inferred transactions
            prev_code = fuzzy_search(
                code, prev_non_inferred_codes.keys(), scorer=fuzz.token_set_ratio
            )
            if prev_code:
                prev_category = prev_non_inferred_codes[prev_code]
                logger.debug(
                    """Found previous non inferred transaction %s with similar code to %s.
                    Using previous category: %s""",
                    prev_code,
                    code,
                    prev_category,
                )
                new_categories.append(prev_category)
                inferred_categories.append(True)
                continue
            # if previous transaction has same code, use that category
            prev_code = fuzzy_search(
                code, prev_inferred_codes.keys(), scorer=fuzz.token_set_ratio
            )
            if prev_code:
                prev_category = prev_inferred_codes[prev_code]
                logger.debug(
                    """Found previous inferred transaction %s with similar code to %s.
                    Using previous category: %s""",
                    prev_code,
                    code,
                    prev_category,
                )
                new_categories.append(prev_category)
                inferred_categories.append(True)
                continue

        if description:
            # Prioritise non-inferred transactions
            prev_description = fuzzy_search(
                description,
                prev_non_inferred_descriptions.keys(),
                scorer=fuzz.token_sort_ratio,
            )
            if prev_description:
                prev_category = prev_non_inferred_descriptions[prev_description]
                logger.debug(
                    """Found previous non inferred transaction %s with similar description to %s.
                    Using previous category: %s""",
                    prev_description,
                    description,
                    prev_category,
                )
                new_categories.append(prev_category)
                inferred_categories.append(True)
                continue
            # if previous transaction has same description, use that category
            prev_description = fuzzy_search(
                description,
                prev_inferred_descriptions.keys(),
                scorer=fuzz.token_sort_ratio,
            )
            if prev_description:
                prev_category = prev_inferred_descriptions[prev_description]
                logger.debug(
                    """Found previous inferred transaction %s with similar description to %s.
                    Using previous category: %s""",
                    prev_description,
                    description,
                    prev_category,
                )
                new_categories.append(prev_category)
                inferred_categories.append(True)
                continue

            # if no previous transaction has same description, use NLP
            result = text_classifier.predict(description, categories)
            logger.debug("Inferred category using NLP for %s: %s", description, result)
            new_categories.append(result)
            inferred_categories.append(True)
            # add to previous transactions
            prev_inferred_descriptions[description] = result
            if code:
                prev_inferred_codes[code] = result
        else:
            logger.debug(
                "Using default category Other as no description was given and couldn't match code. %s",
                row,
            )
            new_categories.append("Other")
            inferred_categories.append(True)
    df["Inferred_Category"] = inferred_categories
    df["Category"] = new_categories
    return df
