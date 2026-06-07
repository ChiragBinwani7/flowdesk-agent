from db.sqlite_manager import (
    get_customer,
    get_plan,
    get_incidents
)

from rag.retriever import search_docs


def handle_refund(customer_id, query):
    customer = get_customer(customer_id)

    return {
        "customer": customer["company_name"],
        "action": "create_ticket",
        "team": "billing-support",
        "priority": "medium",
        "reason": "Refund requests require manual review"
    }


def handle_incident(customer_id, query):
    customer = get_customer(customer_id)

    incidents = get_incidents(
        customer["region"]
    )

    if incidents:
        return {
            "status": "incident_found",
            "region": customer["region"],
            "incidents": incidents
        }

    return {
        "status": "no_incident_found",
        "region": customer["region"]
    }


def handle_export(customer_id, query):
    customer = get_customer(customer_id)

    plan = get_plan(
        customer["plan"]
    )

    docs = search_docs(query)

    return {
        "customer": customer["company_name"],
        "plan": customer["plan"],
        "export_limit":
            plan["limits"]["csv_export_rows"],
        "docs": docs
    }


def handle_sso(customer_id, query):
    customer = get_customer(customer_id)

    docs = search_docs(query)

    return {
        "customer": customer["company_name"],
        "version": customer["product_version"],
        "features": customer["features"],
        "docs": docs
    }


def handle_query(customer_id, query):

    query_lower = query.lower()

    if "refund" in query_lower:
        return handle_refund(
            customer_id,
            query
        )

    if "dashboard" in query_lower:
        return handle_incident(
            customer_id,
            query
        )

    if "fd-4297" in query_lower:
        return handle_export(
            customer_id,
            query
        )

    if "sso" in query_lower:
        return handle_sso(
            customer_id,
            query
        )

    return {
        "status": "unknown_query",
        "query": query
    }


if __name__ == "__main__":

    print("\nREFUND TEST\n")
    print(
        handle_query(
            "cust_1001",
            "Please refund my invoice"
        )
    )

    print("\nINCIDENT TEST\n")
    print(
        handle_query(
            "cust_1001",
            "Dashboard is slow"
        )
    )

    print("\nSSO TEST\n")
    print(
        handle_query(
            "cust_1002",
            "How do I enable SAML SSO?"
        )
    )

    print("\nEXPORT TEST\n")
    print(
        handle_query(
            "cust_1001",
            "FD-4297 export error"
        )
    )