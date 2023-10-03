Bun.serve({
  fetch(req) {
    return new Response(Math.round(Math.random() * 10).toString());
  },
});
