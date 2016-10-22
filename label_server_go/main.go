package main;

import (
    "fmt"
    "os"
    "io/ioutil"
    "net"
)

func main() {
    label, err := ioutil.ReadFile("label.txt")
    if err != nil {
        println("Error reading file.", err.Error())
        os.Exit(1)
    }

    conn, err := net.Dial("tcp", "localhost:5555")
    if err != nil {
        println("Error opening connection: ", err.Error())
        os.Exit(1)
    }
    fmt.Fprintf(conn, string(label))
}
