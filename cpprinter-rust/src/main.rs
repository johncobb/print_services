use std::net::{TcpListener, TcpStream};
use std::io::Read;

fn main() {
    let listener = TcpListener::bind("0.0.0.0:5555").unwrap();

    //listener.incoming is an iterator over the accepts
    for stream in listener.incoming() {
        match stream {
            Ok(mut stream) => {
                handle_connection(&mut stream);
            }
            Err(_) => {println!("Connection error"); }
        }
    }
    println!("Hello, world!");
}

fn handle_connection(stream: &mut TcpStream) {
    let mut label: Vec<u8> = Vec::new();
    let _ = stream.read_to_end(&mut label).unwrap();
    print_label(String::from_utf8(label).unwrap());
}

fn print_label(label: String) {
    println!("{}", label);
}
