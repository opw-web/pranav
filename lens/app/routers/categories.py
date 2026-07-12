
from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser, get_current_user, get_scoped_session
from app.services.categories import (
    MaxDepthError,
    create_category,
    delete_category,
    get_grouped_tree,
    merge_categories,
    rename_category,
    search_with_keywords,
)
from app.services.categorizer import add_keyword, list_keywords, remove_keyword
from app.templating import templates

router = APIRouter()


@router.get("/categories")
async def categories_page(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    tree = await get_grouped_tree(db, user.id)
    return templates.TemplateResponse(request, "categories.html", {"tree": tree})


@router.get("/category-picker")
async def category_picker(
    request: Request,
    q: str = "",
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    query = q.strip()
    if query:
        results, keyword_hits, exact_match = await search_with_keywords(db, user.id, query)
        return templates.TemplateResponse(
            request, "partials/category_picker.html",
            {
                "query": query,
                "results": results,
                "keyword_hits": keyword_hits,
                "exact_match": exact_match,
                "groups": [],
            },
        )
    groups = await get_grouped_tree(db, user.id)
    return templates.TemplateResponse(
        request, "partials/category_picker.html",
        {"query": "", "results": [], "keyword_hits": [], "exact_match": True, "groups": groups},
    )


@router.post("/categories")
async def create_category_route(
    request: Request,
    name: str = Form(...),
    parent_id: str | None = Form(None),
    kind: str = Form("expense"),
    color: str | None = Form(None),
    icon: str | None = Form(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    parent_id = parent_id or None
    try:
        new_cat = await create_category(db, user.id, name, parent_id=parent_id, kind=kind, color=color, icon=icon)
    except MaxDepthError:
        return templates.TemplateResponse(
            request, "partials/toast.html", {"message": "Categories can only be 2 levels deep.", "kind": "error"}
        )

    tree = await get_grouped_tree(db, user.id)
    return templates.TemplateResponse(
        request,
        "partials/category_created.html",
        {"c": {**new_cat, "is_child": bool(parent_id), "label": new_cat["name"]}, "tree": tree},
    )


@router.patch("/categories/{category_id}")
async def rename_category_route(
    request: Request,
    category_id: str,
    name: str = Form(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await rename_category(db, user.id, category_id, name)
    tree = await get_grouped_tree(db, user.id)
    return templates.TemplateResponse(request, "partials/category_tree.html", {"tree": tree})


@router.post("/categories/merge")
async def merge_categories_route(
    request: Request,
    source_id: str = Form(...),
    target_id: str = Form(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await merge_categories(db, user.id, source_id, target_id)
    tree = await get_grouped_tree(db, user.id)
    return templates.TemplateResponse(request, "partials/category_tree.html", {"tree": tree})


@router.delete("/categories/{category_id}")
async def delete_category_route(
    request: Request,
    category_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await delete_category(db, user.id, category_id)
    tree = await get_grouped_tree(db, user.id)
    return templates.TemplateResponse(request, "partials/category_tree.html", {"tree": tree})


@router.post("/categories/{category_id}/keywords")
async def add_keywords_route(
    request: Request,
    category_id: str,
    keyword: str = Form(""),
    keywords: str = Form(""),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    """Add one reason keyword (Form `keyword`) or several at once (comma-separated
    Form `keywords`) to a category (§WS4a). Returns the re-rendered keyword chips
    for just this category."""
    for kw in (keywords or keyword).split(","):
        await add_keyword(db, user.id, category_id, kw)
    chips = await list_keywords(db, user.id, category_id)
    return templates.TemplateResponse(
        request, "partials/category_keywords.html",
        {"category_id": category_id, "keywords": chips},
    )


@router.delete("/categories/{category_id}/keywords/{rule_id}")
async def remove_keyword_route(
    request: Request,
    category_id: str,
    rule_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_scoped_session),
):
    await remove_keyword(db, user.id, rule_id)
    chips = await list_keywords(db, user.id, category_id)
    return templates.TemplateResponse(
        request, "partials/category_keywords.html",
        {"category_id": category_id, "keywords": chips},
    )
