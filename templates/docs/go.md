# Go

Below is an example of making a HTTP request to SITE_NAME from Go.

```go
package main

import "fmt"
import "net/http"
import "time"

func main() {
    var client = &http.Client{
        Timeout: 10 * time.Second,
    }

    _, err := client.Head("PING_URL")
    if err != nil {
        fmt.Printf("%s", err)
    }
}

```
