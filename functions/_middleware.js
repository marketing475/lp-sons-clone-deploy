// URL-consolidation middleware for the ~300 legacy URL variants that
// exceed Cloudflare Pages' _redirects rule cap (~100 on Free tier).
//
// Precedence: static file → _redirects → this middleware → 404.
// Anything _redirects handles never reaches here.
//
// If a rewritten target itself doesn't exist as a page, the client
// still gets the correct 301 followed by a 404 at the destination —
// the same net result as leaving the origin URL to 404 directly,
// but with the redirect signal Google needs to consolidate.

const HOST = "https://lpandsonsautocare.com";

export async function onRequest(context) {
  const { request, next } = context;
  const url = new URL(request.url);
  const path = url.pathname;

  // /blog/{slug}  and  /blog/{slug}.html  →  /{slug}/
  // Consolidates URLs from the ~2-month window blog posts lived under /blog/.
  // Preserves /blog/posts.json and /blog/rss.xml (sidecar data files).
  const blogMatch = path.match(/^\/blog\/([^/]+?)(?:\.html)?$/);
  if (blogMatch) {
    const slug = blogMatch[1];
    if (slug !== "posts.json" && slug !== "rss.xml") {
      return Response.redirect(`${HOST}/${slug}/`, 301);
    }
  }

  // /{slug}.html  →  /{slug}/    (root-level .html from WordPress era)
  const htmlMatch = path.match(/^\/([^/]+)\.html$/);
  if (htmlMatch) {
    const slug = htmlMatch[1];
    if (slug !== "index" && slug !== "404") {
      return Response.redirect(`${HOST}/${slug}/`, 301);
    }
  }

  return next();
}
