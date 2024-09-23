group "default" {
  target = "app"
}

target "app" {
  context = "."
  dockerfile = "Dockerfile"
  builder = "container"
}

NOT IN USE AT THE MOMENT, might be useful in future