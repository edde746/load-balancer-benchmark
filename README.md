# load-balancer-benchmark

A simple benchmark of Nginx, HAProxy, Traefik and Caddy. Somewhat based of [this article](https://www.loggly.com/blog/benchmarking-5-popular-load-balancers-nginx-haproxy-envoy-traefik-and-alb/).

## Running

```bash
git clone https://github.com/edde746/load-balancer-benchmark.git
cd load-balancer-benchmark
docker-compose up -d
pip install -r requirements.txt
python main.py
```

## Results

Results are written to `comparison.html`, you can [view my results here](https://edde746.github.io/load-balancer-benchmark/comparison.html).
