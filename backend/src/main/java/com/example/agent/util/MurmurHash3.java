package com.example.agent.util;

/**
 * MurmurHash3 实现
 * 参考 Apache Doris: be/src/util/hash/murmur_hash3.cpp
 *
 * MurmurHash3 是 Austin Appleby 发布的非加密哈希算法，
 * 具有良好的分布性和雪崩效应，适用于哈希表和布隆过滤器。
 */
public class MurmurHash3 {

    // x86 32-bit hash constants
    private static final int C1_32 = 0xcc9e2d51;
    private static final int C2_32 = 0x1b873593;

    // x64 128-bit hash constants
    private static final long C1_64 = 0x87c37b91114253d5L;
    private static final long C2_64 = 0x4cf5ad432745937fL;

    // x64 mix constants
    private static final long R1_64 = 31;
    private static final long R2_64 = 27;
    private static final long M_64 = 5;
    private static final long FMSED_64 = 0x52dce729L;

    /**
     * x86 32-bit hash
     *
     * @param key   输入数据
     * @param len   数据长度
     * @param seed  种子值
     * @return 32位哈希值
     */
    public static int murmur_hash3_x86_32(byte[] key, int len, int seed) {
        final int nblocks = len >> 2;

        int h1 = seed;

        // body - 向前读取
        for (int i = 0; i < nblocks; i++) {
            int k1 = getInt(key, i << 2);

            k1 *= C1_32;
            k1 = Integer.rotateLeft(k1, 15);
            k1 *= C2_32;

            h1 ^= k1;
            h1 = Integer.rotateLeft(h1, 13);
            h1 = h1 * 5 + 0xe6546b64;
        }

        // tail
        int k1 = 0;
        int tail = nblocks << 2;

        switch (len & 3) {
            case 3:
                k1 ^= (key[tail + 2] & 0xff) << 16;
            case 2:
                k1 ^= (key[tail + 1] & 0xff) << 8;
            case 1:
                k1 ^= (key[tail] & 0xff);
                k1 *= C1_32;
                k1 = Integer.rotateLeft(k1, 15);
                k1 *= C2_32;
                h1 ^= k1;
        }

        // finalization
        h1 ^= len;
        h1 = fmix32(h1);

        return h1;
    }

    /**
     * x86 128-bit hash (返回四个32位值)
     */
    public static int[] murmur_hash3_x86_128(byte[] key, int len, int seed) {
        final int nblocks = len >> 4;

        int h1 = seed, h2 = seed, h3 = seed, h4 = seed;

        // C1-C4 for x86_128 are different
        final int C1 = 0x239b961b;
        final int C2 = 0xab0e9789;
        final int C3 = 0x38b34ae5;
        final int C4 = 0xa1e38b93;

        // body
        for (int i = 0; i < nblocks; i++) {
            int k1 = getInt(key, i * 16);
            int k2 = getInt(key, i * 16 + 4);
            int k3 = getInt(key, i * 16 + 8);
            int k4 = getInt(key, i * 16 + 12);

            k1 *= C1;
            k1 = Integer.rotateLeft(k1, 15);
            k1 *= C2;
            h1 ^= k1;
            h1 = Integer.rotateLeft(h1, 19);
            h1 += h2;
            h1 = h1 * 5 + 0x561ccd1b;

            k2 *= C2;
            k2 = Integer.rotateLeft(k2, 16);
            k2 *= C3;
            h2 ^= k2;
            h2 = Integer.rotateLeft(h2, 17);
            h2 += h3;
            h2 = h2 * 5 + 0x561ccd1b;

            k3 *= C3;
            k3 = Integer.rotateLeft(k3, 18);
            k3 *= C4;
            h3 ^= k3;
            h3 = Integer.rotateLeft(h3, 13);
            h3 += h4;
            h3 = h3 * 5 + 0x561ccd1b;

            k4 *= C4;
            k4 = Integer.rotateLeft(k4, 17);
            k4 *= C1;
            h4 ^= k4;
            h4 = Integer.rotateLeft(h4, 15);
            h4 += h1;
            h4 = h4 * 5 + 0x561ccd1b;
        }

        // tail
        int k1 = 0, k2 = 0, k3 = 0, k4 = 0;
        int tail = nblocks << 4;

        switch (len & 15) {
            case 15: k4 ^= (key[tail + 14] & 0xff) << 24;
            case 14: k4 ^= (key[tail + 13] & 0xff) << 16;
            case 13: k4 ^= (key[tail + 12] & 0xff) << 8;
            case 12: k4 ^= (key[tail + 11] & 0xff);
                k4 *= C4; k4 = Integer.rotateLeft(k4, 17); k4 *= C1; h4 ^= k4;
            case 11: k3 ^= (key[tail + 10] & 0xff) << 24;
            case 10: k3 ^= (key[tail + 9] & 0xff) << 16;
            case 9:  k3 ^= (key[tail + 8] & 0xff) << 8;
            case 8:  k3 ^= (key[tail + 7] & 0xff);
                k3 *= C3; k3 = Integer.rotateLeft(k3, 18); k3 *= C4; h3 ^= k3;
            case 7:  k2 ^= (key[tail + 6] & 0xff) << 24;
            case 6:  k2 ^= (key[tail + 5] & 0xff) << 16;
            case 5:  k2 ^= (key[tail + 4] & 0xff) << 8;
            case 4:  k2 ^= (key[tail + 3] & 0xff);
                k2 *= C2; k2 = Integer.rotateLeft(k2, 16); k2 *= C3; h2 ^= k2;
            case 3:  k1 ^= (key[tail + 2] & 0xff) << 24;
            case 2:  k1 ^= (key[tail + 1] & 0xff) << 16;
            case 1:  k1 ^= (key[tail] & 0xff);
                k1 *= C1; k1 = Integer.rotateLeft(k1, 15); k1 *= C2; h1 ^= k1;
        }

        // finalization
        h1 ^= len; h2 ^= len; h3 ^= len; h4 ^= len;
        h1 += h2; h1 += h3; h1 += h4;
        h2 += h1; h3 += h1; h4 += h1;
        h1 = fmix32(h1); h2 = fmix32(h2); h3 = fmix32(h3); h4 = fmix32(h4);
        h1 += h2; h1 += h3; h1 += h4;
        h2 += h1; h3 += h1; h4 += h1;

        return new int[] { h1, h2, h3, h4 };
    }

    /**
     * x64 64-bit hash - 与 Doris MURMUR_HASH3_64 一致
     *
     * @param key   输入数据
     * @param len   数据长度
     * @param seed  种子值
     * @return 64位哈希值
     */
    public static long murmur_hash3_x64_64(byte[] key, int len, long seed) {
        final int nblocks = len >> 3;

        long h1 = seed;

        // body - 向前读取8字节块
        for (int i = 0; i < nblocks; i++) {
            long k1 = getLong(key, i << 3);

            k1 *= C1_64;
            k1 = Long.rotateLeft(k1, 31);
            k1 *= C2_64;
            h1 ^= k1;

            h1 = Long.rotateLeft(h1, 27);
            h1 = h1 * M_64 + FMSED_64;
        }

        // tail
        long k1 = 0;
        int tail = nblocks << 3;

        switch (len & 7) {
            case 7: k1 ^= (long) (key[tail + 6] & 0xff) << 48;
            case 6: k1 ^= (long) (key[tail + 5] & 0xff) << 40;
            case 5: k1 ^= (long) (key[tail + 4] & 0xff) << 32;
            case 4: k1 ^= (long) (key[tail + 3] & 0xff) << 24;
            case 3: k1 ^= (long) (key[tail + 2] & 0xff) << 16;
            case 2: k1 ^= (long) (key[tail + 1] & 0xff) << 8;
            case 1: k1 ^= (long) (key[tail] & 0xff);
                k1 *= C1_64;
                k1 = Long.rotateLeft(k1, 31);
                k1 *= C2_64;
                h1 ^= k1;
        }

        // finalization
        h1 ^= len;
        h1 = fmix64(h1);

        return h1;
    }

    /**
     * 便捷方法：对字符串进行哈希
     */
    public static long hash64(String str, long seed) {
        byte[] bytes = str.getBytes();
        return murmur_hash3_x64_64(bytes, bytes.length, seed);
    }

    // ====================== 内部辅助方法 ======================

    private static int getInt(byte[] data, int offset) {
        return (data[offset] & 0xff)
                | ((data[offset + 1] & 0xff) << 8)
                | ((data[offset + 2] & 0xff) << 16)
                | ((data[offset + 3] & 0xff) << 24);
    }

    private static long getLong(byte[] data, int offset) {
        return (data[offset] & 0xffL)
                | ((data[offset + 1] & 0xffL) << 8)
                | ((data[offset + 2] & 0xffL) << 16)
                | ((data[offset + 3] & 0xffL) << 24)
                | ((data[offset + 4] & 0xffL) << 32)
                | ((data[offset + 5] & 0xffL) << 40)
                | ((data[offset + 6] & 0xffL) << 48)
                | ((data[offset + 7] & 0xffL) << 56);
    }

    private static int fmix32(int h) {
        h ^= h >>> 16;
        h *= 0x85ebca6b;
        h ^= h >>> 13;
        h *= 0xc2b2ae35;
        h ^= h >>> 16;
        return h;
    }

    private static long fmix64(long h) {
        h ^= h >>> 33;
        h *= 0xff51afd7ed558ccdL;
        h ^= h >>> 33;
        h *= 0xc4ceb9fe1a85ec53L;
        h ^= h >>> 33;
        return h;
    }

    // ====================== 主函数测试 ======================

    public static void main(String[] args) {
        String test = "1234567";
        long seed = 0;  // Doris 默认 seed

        System.out.println("=== MurmurHash3 Test ===");
        System.out.println("Expected from Doris: 685187355594541561");
        System.out.println();

        long hash64 = murmur_hash3_x64_64(test.getBytes(), test.length(), seed);
        System.out.println("x64_64 (seed=0): " + hash64);
        System.out.println();
    }
}
