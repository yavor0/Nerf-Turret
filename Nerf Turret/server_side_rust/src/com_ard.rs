use serialport::{SerialPort, Error};

pub struct ComArd {
    port: Option<Box<dyn SerialPort>>,
}

impl ComArd {

    pub fn connect(port_name: &str, baud_rate: u32) -> Result<Self, Error> {
        let port = serialport::new(port_name, baud_rate).open().expect("Failed to open port");


        Ok(ComArd { port : Some(port)})
    }

    pub fn new() -> Self {
        Self { port: None }
    }

    pub fn send(&mut self, data: &[u8]) -> Result<(), Error> {
        self.port.as_mut().unwrap().write(data)?;
        Ok(())
    }

    fn remap(value_to_map: i32, new_range_min: i32, new_range_max: i32, old_range_min: i32, old_range_max: i32) -> i32 {
        let remapped_val = ((value_to_map - old_range_min) as f64 * (new_range_max - new_range_min) as f64 / (old_range_max - old_range_min) as f64 + new_range_min as f64) as i32;
        if remapped_val > new_range_max {
            new_range_max
        } else if remapped_val < new_range_min {
            new_range_min
        } else {
            remapped_val
        }
    }
}
