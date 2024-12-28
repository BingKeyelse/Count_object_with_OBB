from easymodbus.modbusClient import ModbusClient

class RS485:

    def __init__(self, port="/dev/ttyUSB0", is_rtu=True, ip=None):
        self.port = port
        self.ip = ip
        self.is_rtu = is_rtu
        self.connected_to_plc = False

    def check_connection(self):
        try:
            print("connect")
            plc = ModbusClient(self.port)  # Sử dụng self.port
            
            plc.connect()
            print("connect complete")
            try:
                plc.write_single_coil(13, 1)
                verify_coil = (1 == int(plc.read_coils(13, 1)[0]))
                plc.write_single_register(13, 1)
                verify_reg = (1 == int(plc.read_holdingregisters(13, 1)[0]))
                self.connected_to_plc = (verify_coil and verify_reg)
            except Exception as e:
                print(e)
                self.connected_to_plc = False
            plc.close()
        except Exception as e:
            print(e)
            self.connected_to_plc = False

    def write(self, type_, address, value):
        try:
            plc = ModbusClient(self.port)  # Sử dụng self.port
            plc.connect()

            if type_ == 'coil':
                plc.write_single_coil(address, value)
            elif type_ == 'reg':
                plc.write_single_register(address, value)
            plc.close()

        except Exception as e:
            print(e)
            self.check_connection()
            if self.connected_to_plc:
                self.write(type_, address, value)

    def read(self, type_, address):
        try:
            if self.is_rtu:
                plc = ModbusClient(self.port)  # Sử dụng self.port
            else:
                plc = ModbusClient(self.ip, self.port)
            if not plc.is_connected():
                plc.connect()

            if type_.strip() == 'hr':
                results = plc.read_holdingregisters(address, 1)
            elif type_.strip() == 'ir':
                results = plc.read_inputregisters(address, 1)
            elif type_.strip() == 'coil':
                results = plc.read_coils(address, 9)  #99
            elif type_.strip() == 'coil_single':
                results = plc.read_coils(address, 1)  #99
            elif type_.strip() == 'di':
                results = plc.read_discreteinputs(address, 1)
            else:
                raise Exception("Wrong type")
            plc.close()

            return results

        except Exception as e:
            print(e)

# Tạo đối tượng và gọi phương thức
rs = RS485(port='/dev/ttyS6')
rs.check_connection()  # Gọi phương thức qua đối tượng
