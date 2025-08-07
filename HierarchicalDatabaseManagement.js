
const HierarchicalDatabaseManagement = () => {
    const [hierarchicalData, setHierarchicalData] = useState([]);
    const [selectedMachineType, setSelectedMachineType] = useState(null);
    const [selectedSupplier, setSelectedSupplier] = useState(null);
    const [selectedMachine, setSelectedMachine] = useState(null);

    // Modal states and forms remain the same...

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const hierarchicalDataResponse = await api.get('/api/v1/hierarchical/machine-types');
            setHierarchicalData(hierarchicalDataResponse.data);
        } catch (error) {
            console.error('获取层级数据失败:', error);
            message.error('获取数据失败: ' + error.message);
        }
    };

    const convertToTreeData = (data) => {
        if (!data || data.length === 0) {
            return [];
        }

        return data.map(machineType => ({
            title: machineType.name,
            key: `machine-type-${machineType.id}`,
            children: machineType.suppliers.map(supplier => ({
                title: supplier.name,
                key: `supplier-${supplier.id}`,
                children: supplier.machines.map(machine => ({
                    title: machine.name,
                    key: `machine-${machine.id}`,
                }))
            }))
        }));
    };

    const handleSelectNode = (selectedKeys, info) => {
        if (selectedKeys.length > 0) {
            const key = selectedKeys[0];
            if (key.startsWith('machine-type-')) {
                const machineTypeId = key.split('-')[2];
                const machineType = hierarchicalData.find(mt => mt.id === parseInt(machineTypeId));
                setSelectedMachineType(machineType);
                setSelectedSupplier(null);
                setSelectedMachine(null);
            } else if (key.startsWith('supplier-')) {
                const supplierId = key.split('-')[1];
                let foundSupplier = null;
                let foundMachineType = null;

                for (const machineType of hierarchicalData) {
                    const supplier = machineType.suppliers.find(s => s.id === parseInt(supplierId));
                    if (supplier) {
                        foundSupplier = supplier;
                        foundMachineType = machineType;
                        break;
                    }
                }

                if (foundSupplier && foundMachineType) {
                    setSelectedMachineType(foundMachineType);
                    setSelectedSupplier(foundSupplier);
                    setSelectedMachine(null);
                }
            } else if (key.startsWith('machine-')) {
                const machineId = key.split('-')[1];
                let foundMachine = null;
                let foundSupplier = null;
                let foundMachineType = null;

                for (const machineType of hierarchicalData) {
                    for (const supplier of machineType.suppliers) {
                        const machine = supplier.machines.find(m => m.id === parseInt(machineId));
                        if (machine) {
                            foundMachine = machine;
                            foundSupplier = supplier;
                            foundMachineType = machineType;
                            break;
                        }
                    }
                }

                if (foundMachine && foundSupplier && foundMachineType) {
                    setSelectedMachineType(foundMachineType);
                    setSelectedSupplier(foundSupplier);
                    setSelectedMachine(foundMachine);
                }
            }
        }
    };

    const renderActionButtons = (record) => (
        <Dropdown overlay={
            <Menu>
                <Menu.Item key="edit">
                    <EditOutlined onClick={() => handleEdit(record)} />
                    编辑
                </Menu.Item>
                <Menu.Item key="delete">
                    <DeleteOutlined onClick={() => handleDelete(record)} />
                    删除
                </Menu.Item>
            </Menu>
        }>
            <Button type="link">操作</Button>
        </Dropdown>
    );

    const columns = [
        {
            title: 'PartNumber',
            dataIndex: 'partNumber',
            key: 'partNumber',
        },
        {
            title: '板卡名称',
            dataIndex: 'boardName',
            key: 'boardName',
        },
        {
            title: '单价',
            dataIndex: 'unitPrice',
            key: 'unitPrice',
        },
        {
            title: '操作',
            dataIndex: 'actions',
            key: 'actions',
            render: (_, record) => renderActionButtons(record),
        },
    ];

    return (
        <div className="hierarchical-database-management">
            {/* 左侧供应商列表 */}
            <Card title="供应商列表" extra={<Button type="primary" onClick={handleAddSupplier}>添加</Button>}>
                <List
                    dataSource={suppliers}
                    renderItem={(item) => (
                        <List.Item>
                            {item.name}
                            <span style={{ marginLeft: 10 }}>
                                {renderActionButtons(item)}
                            </span>
                        </List.Item>
                    )}
                />
            </Card>

            {/* 中间设备型号列表 */}
            <Card title="设备型号列表" extra={<Button type="primary" onClick={handleAddMachine}>添加</Button>}>
                <List
                    dataSource={machines}
                    renderItem={(item) => (
                        <List.Item>
                            {item.name}
                            <span style={{ marginLeft: 10 }}>
                                {renderActionButtons(item)}
                            </span>
                        </List.Item>
                    )}
                />
            </Card>

            {/* 右侧板卡配置详情 */}
            <Card title="板卡配置详情" extra={<Button type="primary" onClick={handleAddCardConfig}>添加</Button>}>
                <Table columns={columns} dataSource={cardConfigs} />
            </Card>
        </div>
    );
};

export default HierarchicalDatabaseManagement;