group "default" {
  target = "app"
}

target "app" {
  context = "."
  dockerfile = "Dockerfile"
  builder = "container"
}