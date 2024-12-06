from locust import HttpUser, task

exist_pid = "6707956239445e8693a16362"
exist_uid = "671210a24c0b7d4a8caa715a"
extra_uid = "671210b74c0b7d4a8caa715b"


class WebsiteUser(HttpUser):
    @task(2)
    def get_products(self):
        self.client.get("/products/")

    @task(2)
    def get_cart(self):
        self.client.get(f"/cart/{exist_uid}/")

    @task(2)
    def add_cart(self):
        data = {"uid": extra_uid, "pid": exist_pid, "quantity": 1}
        self.client.post("/cart/add/", json=data)
