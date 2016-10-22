use std::net::TcpStream;
use std::io::prelude::*;
use std::fs::File;
fn main() {
    write_to_device("localhost".to_string(), "5555".to_string(), "stuff".to_string());
    println!("Hello, world!");
}

fn write_to_device(host: String, port: String, label: String) {
    let host = format!("{}:{}", host, port);
    let mut stream = TcpStream::connect(host.as_str()).unwrap();
    let _ = stream.write(label.as_bytes());
}
