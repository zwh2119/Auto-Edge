# Data Generator for Auto-Edge

## Brief Introduction


## Quick Start
```python

```

## Docker Start
```shell

```

## Data Structure

```
                1.source_id
                2.task_id
                3.priority 
                4.metadata:{resolution_raw, fps_raw, resolution, frame_number,
                            skip_interval, encoding}
                
                5.pipeline_flow:[service1, service2,..., end]
                    service:{service_name, execute_address, execute_data}
                    execute_data:{service_time, transmit_time, acc}
                6.cur_flow_index
                7.scenario_data:{obj_num, obj_size, stable}
                8.content_data (middle_result/result)
                9.tmp_data:{} (middle_record)
```
