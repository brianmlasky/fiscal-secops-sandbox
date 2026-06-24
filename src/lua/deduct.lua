local start_time = tonumber(redis.call('time')[1])

local balance_raw = redis.call('get', KEYS[1])
local balance

if balance_raw then
    balance = tonumber(balance_raw)
    if not balance then
        return {0, 0, 0, "CORRUPTED"}
    end
else
    balance = 0
end

local cost = tonumber(ARGV[1])
local request_id = ARGV[2]
local family_id = ARGV[3]

-- 1. Strict Request Idempotency
local idempotency_key = "idempotency:" .. KEYS[1] .. ":" .. request_id
local previous_result = redis.call('get', idempotency_key)
if previous_result then
    local cached = cjson.decode(previous_result)
    return {cached.new_balance, cached.prev_balance, cached.was_success, "CACHE_HIT"}
end

local family_key = "family:" .. KEYS[1] .. ":" .. family_id
local family_ack_key = family_key .. ":ack"
local lock_timestamp_key = family_key .. ":ts"

-- 2. ATOMIC LOCK ACQUISITION with ACK and TIMEOUT
local lock_acquired = redis.call('set', family_key, "PROCESSING", "NX", "EX", 86400)

if not lock_acquired then
    local ack = redis.call('get', family_ack_key)
    
    if ack then
        local cached_family = cjson.decode(ack)
        local result = {
            cached_family.new_balance,
            cached_family.prev_balance,
            cached_family.was_success,
            "FAMILY_HIT"
        }
        redis.call('setex', idempotency_key, 86400, cjson.encode(result))
        return result
    end

    -- Gap 1 Fix: Detect Lock Holder Timeout (>30 seconds)
    local lock_ts = redis.call('get', lock_timestamp_key)
    if lock_ts then
        local elapsed = start_time - tonumber(lock_ts)
        if elapsed > 30 then
            return {0, 0, 0, "TIMEOUT"}
        end
    end
    
    return {0, 0, 0, "PROCESSING"}
end

-- Winner publishes lock timestamp for timeout detection
redis.call('set', lock_timestamp_key, start_time, "EX", 86400)

-- 3. Execute Deduction
local was_success = false
local prev_balance = balance
local new_balance = balance

if balance >= cost then
    redis.call('decrby', KEYS[1], cost)
    new_balance = balance - cost
    was_success = true
end

-- Gap 2 Fix: Refresh TTL if execution took an exceptionally long time
local end_time = tonumber(redis.call('time')[1])
local execution_duration = end_time - start_time
local ttl = math.max(86400, execution_duration + 300)

-- 4. Winner publishes result and ACK
local result = {new_balance, prev_balance, was_success, "SUCCESS"}
local family_data = {
    new_balance = new_balance,
    prev_balance = prev_balance,
    was_success = was_success
}

redis.call('set', family_key, cjson.encode(family_data), "EX", ttl)
redis.call('set', family_ack_key, cjson.encode(family_data), "EX", ttl)
redis.call('set', idempotency_key, cjson.encode(result), "EX", ttl)

return result
