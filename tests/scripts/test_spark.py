"""
Test the creation and utilization of a SparkContext.
"""
import pytest

pytestmark = pytest.mark.skip

import pandas as pd
from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession, SQLContext

if __name__ == "__main__":
 
    sc = SparkContext.getOrCreate()

    sqlContext = SQLContext(sc)
    spark = sqlContext.sparkSession
    
    df = pd.DataFrame([1, 2, 3, 4, 5], columns=['a'])
    
    df['a'] = df['a'].astype(int)
    
    sdf = spark.createDataFrame(df)
    
    sdf.show()
