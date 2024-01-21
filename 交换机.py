def get_vlan_range(vlan_input):
    # 简化 VLAN 输入验证，根据实际需求调整
    vlan_list = vlan_input.split()
    if not all([v.isdigit() for v in vlan_list]):
        raise ValueError("VLAN 输入格式不正确，请输入数字，并用空格分隔")
    return vlan_list

def process_device_config(num_devices):
    for i in range(num_devices):
        sysname = input(f'请输入设备名（针对设备{i+1}）：')
        confi = f"sys\nsysname {sysname}\n"
        device = input('请选择交换机（输入1）&路由器（输入2）')

        with open(f"config_{sysname}_{i}.txt", "a") as f:
            if device == '1':
                vlan = input("请输入要创建的VLAN（空格隔开）：")
                vlans = get_vlan_range(vlan)
                confi += f"vlan batch {' '.join(vlans)} \n"

                ethyes = input("是否创建链路聚合，请输入1（是）或2（否）")
                if ethyes == '1':
                    ethnum = int(input("请输入聚合口数量"))
                    for k in range(ethnum):
                        ethnumber = input("请输入聚合口的编号")
                        ethmode = input("请输入聚合口的模式")
                        config = f"interface eth-trunk {ethnum} \n mode {ethmode} \n"
                        trunknum1 = input("请输入起始聚合接口")
                        trunknum2 = input("请输入终止聚合接口")
                        config += f"trunkport GigabitEthernet {trunknum1} to {trunknum2} \n"
                        confi += config

                while True:
                    interface_name = input('请输入接口名称（输入"q"退出）：')
                    if interface_name == "q":
                        break
                    interface_type = int(input('请输入接口类型（1-access/2-trunk）：'))
                    if interface_type not in [1, 2]:
                        print("输入错误，请输入1或2")
                        continue
                    
                    interface_type_str = ('access', 'trunk')[interface_type - 1]
                    
                    if interface_type_str == "access":
                        vlan = input('请输入接口所属的VLAN：')
                        confi += f"interface  {interface_name} \n port link-type {interface_type_str}\n port default vlan {vlan} \n"
                        switch_ip_query = input('是否需要配置IP，请输入1（是）或2（否）')
                        if switch_ip_query == '1':
                            int_ip = input('IP地址是：')
                            confi += f"interface vlanif {vlan} \n ip address {int_ip}\n"
                    else:
                        allowed_vlans = input('请输入接口放行的VLAN（多个VLAN用空格分隔）：')
                        allowed_vlans_list = get_vlan_range(allowed_vlans)
                        confi += f"interface {interface_name} \n port link-type {interface_type_str} \n"
                        confi += f" port trunk allow-pass vlan {' '.join(allowed_vlans_list)} \n"
                        switch_ip_query = input('是否需要配置IP，请输入1（是）或2（否）')
                        if switch_ip_query == '1':
                            for value in allowed_vlans_list:
                                int_ip = input(f'请输入vlanif {value}的IP地址：')
                                confi += f"interface vlanif {value}\n ip address {int_ip}\n"

                    confi += "\n"

            else:  # 处理路由器接口部分
                while True:
                    interface_name2 = input('请输入接口名称（输入"q"退出）：')
                    if interface_name2 == "q":
                        break
                    interface_ip = input('请输入接口IP：')
                    confi += f"interface {interface_name2} \n ip address {interface_ip}\n\n"

            # 静态路由配置
            route_loop = True
            while route_loop:
                route = input("是否需要配置静态路由(输入1代表是，输入2代表否)")
                if route == '2':
                    route_loop = False
                else:
                    destination = input("目的网段 掩码：")
                    next_hop = input("下一跳：")
                    confi += f"ip route-static {destination}  {next_hop}\n\n"

            # MSTP配置
            mstp = input("是否需要配置MSTP(输入1代表是，输入2代表否)")
            if mstp == '1':
                instance_value = int(input("请输入实例数量"))
                confi += f"stp region-configuration\n region-name huawei\n revision-level 12\n"
                for j in range(instance_value):
                    instance_vlan = input(f"请输入实例{j+1}绑定的vlan：")
                    confi += f" instance {j+1} vlan {instance_vlan}\n"
                confi += f" active region-configuration\n"
                for j in range(instance_value):
                    root_status = input(f"请选择实例{j+1}是否为根桥（1代表主根，2代表备份根，3代表非根桥）：")
                    if root_status == '1':
                        confi += f" instance {j+1} root primary\n"
                    elif root_status == '2':
                        confi += f" instance {j+1} root secondary\n\n"

                

            # VRRP配置
            vrrp_dict = {}
            if device == '1' and input("是否需要配置vrrp(输入1代表是，输入2代表否)") == '1':
                for value in vlans:
                    virtual_ip = input(f'请输入vlanif {value}的virtual ip：')
                    vrrp_pri = input("请输入VRRP的优先级")
                    vrrp_dict[value] = {"virtual-ip": virtual_ip, "priority": vrrp_pri}
                
                for vlan, vrrp_info in vrrp_dict.items():
                    confi += f"interface vlanif {vlan}\n"
                    confi += f"vrrp vrid {vlan} virtual-ip {vrrp_info['virtual-ip']}\n"
                    confi += f"vrrp vrid {vlan} priority {vrrp_info['priority']}\n\n"

            # OSPF配置
            ospf = input("是否需要配置ospf(输入1代表是，输入2代表否)")
            if ospf == '1':
                router_id = input(f'请输入router_id:')
                default_route = input("是否需要宣告缺省路由:")
                confi += f"ospf 1 router-id {router_id}\n"
                if default_route == '1':
                    confi += f"default-route-advertise always\n "
                area = input(f'请输入区域')
                confi += f"area {area}\n"
                netnum = int(input(f"请输入要宣告几个网段"))
                for _ in range(netnum):
                    network = input("请输入宣告地址信息")
                    confi += f"network {network}\n"

            # 写入所有配置到文件
            f.write(confi)

        print(f"设备{i + 1}的配置已保存到config_{sysname}_{i}.txt文件中")

# 主程序入口
num_devices = int(input("请输入要导出的设备数量："))
process_device_config(num_devices)